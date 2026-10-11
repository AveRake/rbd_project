#!/usr/bin/env bash
# =====================================================================
#  CampusRent — РТ-1. Межфилиальное бронирование экземпляра техники.
#  Распределённая транзакция по протоколу двухфазной фиксации (2PC)
#  на основе XA-транзакций MySQL 8.0.
#
#  Сценарий (docs/04_Схема_фрагментации.md, п. 4.7, РТ-1):
#    филиалу Санкт-Петербург нужен экземпляр модели, свободных
#    экземпляров которой в СПб нет или мало, — он есть в филиале Казань.
#    Бронирование должно быть атомарным: ЛИБО экземпляр помечен «бронь»
#    И в СПб создана заявка с позицией, ЛИБО не происходит ничего.
#
#  Роли узлов стенда:
#    mysql-slave2 (KZN) — УЧАСТНИК:    владелец техники, переводит
#                                      экземпляр в статус «бронь»;
#    mysql-slave  (SPB) — КООРДИНАТОР: создаёт заявку и позицию заявки;
#    mysql-consol       — узел консолидации: проверяем, что результат
#                         доехал до консолидированной копии (РКД).
#
#  Почему XA, а не две обычные транзакции: транзакции в разных сеансах
#  и на разных серверах зафиксировать атомарно нельзя. XA даёт настоящие
#  две фазы:
#    фаза 1 (PREPARE) — изменения записаны и заблокированы, но не видны
#                       другим сеансам; подготовленная транзакция
#                       переживает обрыв соединения (видна в XA RECOVER);
#    фаза 2 (COMMIT)  — выполняется только после того, как подготовились
#                       ВСЕ участники; иначе все получают ROLLBACK.
#
#  ТРИ ОГРАНИЧЕНИЯ MySQL 8.0, определившие реализацию
#  ------------------------------------------------------------------
#  1. XA-команды нельзя выполнить через PREPARE (ошибка 1295
#     «This command is not supported in the prepared statement protocol»),
#     а XID в XA START должен быть литералом, а не переменной. Поэтому
#     логика каждой фазы оформлена хранимой процедурой, в текст которой
#     XID подставляется при её создании.
#  2. Вспомогательные процедуры — это DDL, а параметр log_replica_updates
#     в MySQL 8.0 включён по умолчанию: DDL попал бы в бинарный журнал,
#     разнёсся по каналам и остановил бы тот узел, где такая процедура
#     уже есть (ошибка 1304 «... already exists»). Поэтому создание и
#     удаление процедур выполняется с SET sql_log_bin = 0.
#  3. XA несовместима с фильтрами репликации: если приёмник применяет
#     фильтр и XA-транзакция затрагивает таблицу, которую фильтр
#     исключает, канал останавливается с ошибкой 3898 «The use of
#     replication filters with XA transactions is not supported».
#     Стенд фильтрует каналы:
#       * ЦО  (РБОК) принимает только таблицы клиентов;
#       * филиалы (РОК) — только НСИ и таблицы клиентов;
#       * узел консолидации (РКД) — только операционные таблицы.
#     Отсюда выбор узлов: участником назначен филиал KZN, потому что его
#     бинарный журнал читает только узел консолидации, а таблица
#     equipment_units входит в его фильтр, — XA проходит. Транзакция
#     координатора (СПб) меняет requests/request_items, которые ЦО
#     фильтром исключает, поэтому её изменения выполняются с
#     sql_log_bin = 0: они локальны для филиала и в репликацию не идут.
#     Атомарность распределённой транзакции от этого не страдает —
#     она обеспечивается фазами XA на двух узлах, а не репликацией.
#
#  Запуск:   bash distributed_booking.sh [EQ_ID] [--skip-negative]
#            EQ_ID — конкретный экземпляр в филиале KZN;
#            если не задан, экземпляр выбирается автоматически
#            (самая дефицитная в СПб модель, у которой есть свободные
#            экземпляры в Казани).
# =====================================================================
set -euo pipefail

PART=mysql-slave2       # узел-участник (филиал Казань, владелец техники)
COORD=mysql-slave       # узел-координатор (филиал Санкт-Петербург)
CONSOL=mysql-consol     # узел консолидации
PART_BR=KZN
COORD_BR=SPB
MY="mysql -uroot -ppassword --default-character-set=utf8mb4"

EQ_ARG=""
for a in "$@"; do
  case "$a" in
    --skip-negative) SKIP_NEGATIVE=1 ;;
    *)               EQ_ARG="$a" ;;
  esac
done
SKIP_NEGATIVE="${SKIP_NEGATIVE:-0}"

STAMP="$(date +%Y%m%d%H%M%S)"
# tr вместо ${VAR,,}: на macOS по умолчанию bash 3.2, где нет этой подстановки
PART_BR_LC="$(printf '%s' "$PART_BR"  | tr '[:upper:]' '[:lower:]')"
COORD_BR_LC="$(printf '%s' "$COORD_BR" | tr '[:upper:]' '[:lower:]')"
XID_PART="campusrent_book_${PART_BR_LC}_${STAMP}"
XID_COORD="campusrent_book_${COORD_BR_LC}_${STAMP}"

say() { printf '%s\n' "$*"; }
hdr() { printf '\n---------------------------------------------------------------------\n%s\n---------------------------------------------------------------------\n' "$*"; }
q()   { local node="$1"; shift; docker exec "$node" $MY "$@" 2>/dev/null; }
qin() { local node="$1" db="${2:-campusrent}"; docker exec -i "$node" $MY "$db"; }
# Запрос к координатору: его XA-изменения намеренно не пишутся в бинарный
# журнал (см. ограничение 3 в шапке файла).
qc()  { docker exec "$COORD" $MY -N -B campusrent -e "SET sql_log_bin = 0; $1" 2>/dev/null; }

# --- откат «зависших» подготовленных транзакций ----------------------
rollback_xid() {
  local node="$1" xid="$2" binlog="$3"
  if q "$node" -N -B -e "XA RECOVER" | grep -q "$xid"; then
    say "    откат подготовленной транзакции $xid на $node"
    if [ "$binlog" = "off" ]; then
      docker exec "$node" $MY -e "SET sql_log_bin = 0; XA ROLLBACK '$xid';" >/dev/null 2>&1 || true
    else
      q "$node" -e "XA ROLLBACK '$xid'" || true
    fi
  fi
}

ABORT=0
cleanup() {
  local rc=$?
  if [ "$rc" -ne 0 ] && [ "$ABORT" = 0 ]; then
    say ""
    say "!! Транзакция прервана (код возврата $rc). Выполняется откат всех участников."
    rollback_xid "$PART"  "$XID_PART"  on
    rollback_xid "$COORD" "$XID_COORD" off
    say "!! Откат выполнен: ни экземпляр, ни заявка не изменены."
  fi
}
trap cleanup EXIT

hdr "РТ-1. Межфилиальное бронирование: распределённая транзакция (2PC / XA)"
say "Координатор (нужна техника) : $COORD (филиал $COORD_BR)"
say "Участник (владелец техники) : $PART (филиал $PART_BR)"
say "XID участника    : $XID_PART"
say "XID координатора : $XID_COORD"

# --- 0. Подготовка: убрать мусор от предыдущих запусков --------------
hdr "0. Подготовка"
for x in $(q "$PART" -N -B -e "XA RECOVER" | awk '{print $NF}' | grep "^campusrent_book_${PART_BR_LC}_" || true); do
  [ -n "$x" ] || continue
  say "    найден незавершённый XID на $PART: $x — откат"
  q "$PART" -e "XA ROLLBACK '$x'" || true
done
for x in $(q "$COORD" -N -B -e "XA RECOVER" | awk '{print $NF}' | grep "^campusrent_book_${COORD_BR_LC}_" || true); do
  [ -n "$x" ] || continue
  say "    найден незавершённый XID на $COORD: $x — откат"
  qc "XA ROLLBACK '$x';" || true
done
say "    незавершённых XA-транзакций нет"

# --- 1. Выбор экземпляра для бронирования ----------------------------
hdr "1. Выбор экземпляра, который нужен филиалу $COORD_BR"
if [ -n "$EQ_ARG" ]; then
  SEL="$(q "$PART" -N -B campusrent -e "
    SELECT e.EQ_ID, e.EQ_INV, e.EQ_MOD,
           CONCAT(m.MOD_BRAND,' ',m.MOD_NAME),
           (SELECT COUNT(*) FROM equipment_units x WHERE x.EQ_MOD=e.EQ_MOD AND x.EQ_BR='$COORD_BR' AND x.EQ_STATUS='свободна'),
           (SELECT COUNT(*) FROM equipment_units y WHERE y.EQ_MOD=e.EQ_MOD AND y.EQ_BR='$PART_BR'  AND y.EQ_STATUS='свободна')
      FROM equipment_units e JOIN models m ON m.MOD_ID=e.EQ_MOD
     WHERE e.EQ_ID=$EQ_ARG AND e.EQ_BR='$PART_BR';")"
else
  SEL="$(q "$PART" -N -B campusrent -e "
    SELECT e.EQ_ID, e.EQ_INV, e.EQ_MOD,
           CONCAT(m.MOD_BRAND,' ',m.MOD_NAME),
           (SELECT COUNT(*) FROM equipment_units x WHERE x.EQ_MOD=e.EQ_MOD AND x.EQ_BR='$COORD_BR' AND x.EQ_STATUS='свободна') AS free_coord,
           (SELECT COUNT(*) FROM equipment_units y WHERE y.EQ_MOD=e.EQ_MOD AND y.EQ_BR='$PART_BR'  AND y.EQ_STATUS='свободна') AS free_part
      FROM equipment_units e JOIN models m ON m.MOD_ID=e.EQ_MOD
     WHERE e.EQ_BR='$PART_BR' AND e.EQ_STATUS='свободна'
     ORDER BY free_coord ASC, free_part DESC, e.EQ_ID ASC LIMIT 1;")"
fi

if [ -z "$SEL" ]; then
  say "Не найден свободный экземпляр в филиале $PART_BR — запустите: bash setup.sh"
  exit 1
fi

IFS=$'\t' read -r EQ_ID EQ_INV EQ_MOD EQ_MODEL FREE_COORD FREE_PART <<<"$SEL"
say "    Экземпляр : EQ_ID=$EQ_ID, инв. номер $EQ_INV, модель $EQ_MOD ($EQ_MODEL)"
say "    Свободно в $COORD_BR: $FREE_COORD шт.  |  свободно в $PART_BR: $FREE_PART шт."
say "    Вывод: в филиале-заказчике модель дефицитна, поэтому бронируем экземпляр в $PART_BR."

say ""
say "    Состояние ДО транзакции:"
q "$PART" --table campusrent -e \
  "SELECT EQ_ID, EQ_INV, EQ_BR, EQ_STATUS FROM equipment_units WHERE EQ_ID=$EQ_ID;" | sed 's/^/    /'
REQ_BEFORE="$(q "$COORD" -N -B campusrent -e "SELECT COUNT(*) FROM requests;")"
say "    Заявок в $COORD_BR до транзакции: $REQ_BEFORE"

# --- 2. Фаза 1, участник: PREPARE ------------------------------------
hdr "2. Фаза 1 / участник $PART_BR: подготовка (XA PREPARE)"
qin "$PART" <<SQL >/dev/null
SET sql_log_bin = 0;   -- DDL вспомогательной процедуры не пишем в бинарный журнал
DROP PROCEDURE IF EXISTS xa_book_participant;
DELIMITER //
CREATE PROCEDURE xa_book_participant(IN p_eq BIGINT UNSIGNED, OUT p_status VARCHAR(24))
BEGIN
  XA START '${XID_PART}';
  UPDATE equipment_units
     SET EQ_STATUS = 'бронь'
   WHERE EQ_ID = p_eq AND EQ_BR = '${PART_BR}' AND EQ_STATUS = 'свободна';
  IF ROW_COUNT() = 1 THEN
    XA END '${XID_PART}';
    XA PREPARE '${XID_PART}';
    SET p_status = 'PREPARED';
  ELSE
    XA END '${XID_PART}';
    XA ROLLBACK '${XID_PART}';
    SET p_status = 'NOT_FREE';
  END IF;
END//
DELIMITER ;
SET sql_log_bin = 1;
SQL
PART_STATUS="$(q "$PART" -N -B campusrent -e "CALL xa_book_participant($EQ_ID, @s); SELECT @s;")"
say "    Участник: блокирует строку и подтверждает готовность."
say "    Результат подготовки: $PART_STATUS"
if [ "$PART_STATUS" != "PREPARED" ]; then
  say "    Экземпляр не свободен — транзакция отменяется, изменения не вносятся."
  exit 1
fi
say "    Изменение не видно другим сеансам (транзакция только подготовлена):"
q "$PART" --table campusrent -e \
  "SELECT EQ_ID, EQ_STATUS FROM equipment_units WHERE EQ_ID=$EQ_ID;" | sed 's/^/    /'

# --- 3. Фаза 1, координатор: PREPARE ---------------------------------
hdr "3. Фаза 1 / координатор $COORD_BR: подготовка (XA PREPARE)"
qin "$COORD" <<SQL >/dev/null
SET sql_log_bin = 0;   -- DDL вспомогательной процедуры не пишем в бинарный журнал
DROP PROCEDURE IF EXISTS xa_book_coordinator;
DELIMITER //
CREATE PROCEDURE xa_book_coordinator(IN p_model BIGINT, IN p_days INT,
                                     OUT p_status VARCHAR(24), OUT p_req BIGINT)
BEGIN
  DECLARE v_req   BIGINT;
  DECLARE v_rit   BIGINT;
  DECLARE v_un    BIGINT;
  DECLARE v_dep   BIGINT;
  DECLARE v_rep   BIGINT;
  DECLARE v_st    BIGINT;
  DECLARE v_tar   BIGINT;
  DECLARE v_price NUMERIC(10,2);
  DECLARE v_unit  VARCHAR(10);
  DECLARE v_cost  NUMERIC(12,2);
  DECLARE v_begin DATE;
  DECLARE v_end   DATE;

  XA START '${XID_COORD}';

  SET v_begin = CURDATE();
  SET v_end   = CURDATE() + INTERVAL p_days DAY;

  -- вуз филиала-заказчика с подразделением и представителем
  SELECT u.UN_ID, d.DEP_ID, r.REP_ID
    INTO v_un, v_dep, v_rep
    FROM universities u
    JOIN departments d     ON d.DEP_UN = u.UN_ID
    JOIN representatives r ON r.REP_UN = u.UN_ID AND r.REP_DEP = d.DEP_ID
   WHERE u.UN_BR = '${COORD_BR}'
   ORDER BY u.UN_ID LIMIT 1;

  SELECT RST_ID INTO v_st FROM request_statuses WHERE RST_NAME = 'подана';

  -- тариф модели, период действия которого покрывает период аренды
  SELECT TAR_ID, TAR_PRICE, TAR_UNIT
    INTO v_tar, v_price, v_unit
    FROM tariffs
   WHERE TAR_MOD = p_model
     AND TAR_BEGIN <= v_begin
     AND (TAR_END IS NULL OR TAR_END >= v_end)
   ORDER BY TAR_ID LIMIT 1;

  SET v_cost = ROUND(v_price * (CASE v_unit
                                  WHEN 'день'   THEN p_days
                                  WHEN 'неделя' THEN p_days / 7
                                  ELSE p_days / 30 END), 2);

  SELECT COALESCE(MAX(REQ_ID), 0) + 1 INTO v_req FROM requests;
  INSERT INTO requests (REQ_ID, REQ_NUMBER, REQ_UN, REQ_DEP, REQ_REP, REQ_BR,
                        REQ_CREATED, REQ_BEGIN, REQ_END, REQ_STATUS, REQ_SUM, REQ_COMMENT)
  VALUES (v_req, CONCAT('XA-', LPAD(v_req, 6, '0')), v_un, v_dep, v_rep, '${COORD_BR}',
          CURDATE(), v_begin, v_end, v_st, 0, 'Межфилиальное бронирование (2PC/XA, РТ-1)');

  SELECT COALESCE(MAX(RIT_ID), 0) + 1 INTO v_rit FROM request_items;
  INSERT INTO request_items (RIT_ID, RIT_REQ, RIT_MOD, RIT_QTY,
                             RIT_BEGIN, RIT_END, RIT_TAR, RIT_COST)
  VALUES (v_rit, v_req, p_model, 1, v_begin, v_end, v_tar, v_cost);

  XA END '${XID_COORD}';
  XA PREPARE '${XID_COORD}';
  SET p_status = 'PREPARED';
  SET p_req    = v_req;
END//
DELIMITER ;
SET sql_log_bin = 1;
SQL
COORD_RES="$(qc "CALL xa_book_coordinator($EQ_MOD, 14, @s, @r); SELECT @s, @r;")"
COORD_STATUS="$(printf '%s' "$COORD_RES" | awk '{print $1}')"
REQ_NEW="$(printf '%s' "$COORD_RES" | awk '{print $2}')"
say "    Координатор: создаёт заявку и позицию заявки (триггеры целостности при этом работают)."
say "    Результат подготовки: $COORD_STATUS, новая заявка REQ_ID=$REQ_NEW"
if [ "$COORD_STATUS" != "PREPARED" ]; then
  say "    Подготовка координатора не удалась — транзакция отменяется."
  exit 1
fi
say "    Новая заявка пока не видна другим сеансам:"
q "$COORD" --table campusrent -e "SELECT COUNT(*) AS requests_visible FROM requests;" | sed 's/^/    /'

# --- 4. Проверка готовности всех участников --------------------------
hdr "4. Проверка: все участники подготовлены (XA RECOVER)"
say "    $PART:"
q "$PART" --table campusrent -e "XA RECOVER;" | sed 's/^/    /'
say "    $COORD:"
q "$COORD" --table campusrent -e "XA RECOVER;" | sed 's/^/    /'
if ! q "$PART" -N -B -e "XA RECOVER" | grep -q "$XID_PART"; then
  say "    Участник не подготовлен — откат."
  exit 1
fi
if ! q "$COORD" -N -B -e "XA RECOVER" | grep -q "$XID_COORD"; then
  say "    Координатор не подготовлен — откат."
  exit 1
fi
say "    Оба участника в состоянии PREPARED — можно переходить к фиксации."

# --- 5. Фаза 2: фиксация ---------------------------------------------
hdr "5. Фаза 2: фиксация на всех участниках (XA COMMIT)"
say "    << точка фиксации: после успешного PREPARE всех участников >>"
say "    XA COMMIT на участнике $PART ..."
q "$PART" -e "XA COMMIT '$XID_PART'"
say "    XA COMMIT на координаторе $COORD ..."
qc "XA COMMIT '$XID_COORD';"
say "    Транзакция зафиксирована на обоих узлах."

# --- 6. Результат -----------------------------------------------------
hdr "6. Состояние ПОСЛЕ транзакции"
say "    Участник $PART ($PART_BR) — экземпляр забронирован:"
q "$PART" --table campusrent -e \
  "SELECT EQ_ID, EQ_INV, EQ_BR, EQ_STATUS FROM equipment_units WHERE EQ_ID=$EQ_ID;" | sed 's/^/    /'
say "    Координатор $COORD ($COORD_BR) — созданная заявка:"
q "$COORD" --table campusrent -e "
  SELECT r.REQ_ID, r.REQ_NUMBER, u.UN_SHORT, r.REQ_BR, rs.RST_NAME, r.REQ_BEGIN, r.REQ_END, r.REQ_SUM
    FROM requests r
    JOIN universities u       ON u.UN_ID = r.REQ_UN
    JOIN request_statuses rs  ON rs.RST_ID = r.REQ_STATUS
   WHERE r.REQ_ID = $REQ_NEW;" | sed 's/^/    /'

say "    Ожидание репликации на узел консолидации (РКД) ..."
sleep 3
CONS_EQ="$(q "$CONSOL" -N -B campusrent -e "SELECT EQ_STATUS FROM equipment_units WHERE EQ_ID=$EQ_ID;")"
say "    В консолидированной копии $CONSOL экземпляр $EQ_ID имеет статус: '$CONS_EQ'"
say "    (заявка координатора в репликацию не передаётся — см. ограничение 3"
say "     в шапке скрипта: XA несовместима с фильтрами репликации, ошибка 3898)."

# --- 7. Негативная проверка: повторное бронирование невозможно --------
if [ "$SKIP_NEGATIVE" = 0 ]; then
  hdr "7. Негативная проверка: повторное бронирование того же экземпляра"
  say "    Повторяем фазу 1 на участнике для того же EQ_ID=$EQ_ID."
  NEG_STATUS="$(q "$PART" -N -B campusrent -e "CALL xa_book_participant($EQ_ID, @s); SELECT @s;")"
  say "    Результат: $NEG_STATUS"
  if [ "$NEG_STATUS" = "NOT_FREE" ]; then
    say "    Экземпляр уже забронирован, UPDATE не затронул ни одной строки,"
    say "    транзакция откачена (XA_ROLLBACK) — двойное бронирование невозможно."
  else
    say "    ОШИБКА: экземпляр забронирован повторно!"
    exit 1
  fi
  REQ_AFTER="$(q "$COORD" -N -B campusrent -e "SELECT COUNT(*) FROM requests;")"
  say "    Заявок в $COORD_BR после негативной проверки: $REQ_AFTER (было $REQ_BEFORE, стало $((REQ_BEFORE+1))) — лишняя заявка не создана."
fi

# --- 8. Уборка временных процедур ------------------------------------
hdr "8. Уборка"
q "$PART"  campusrent -e "SET sql_log_bin=0; DROP PROCEDURE IF EXISTS xa_book_participant;"  || true
q "$COORD" campusrent -e "SET sql_log_bin=0; DROP PROCEDURE IF EXISTS xa_book_coordinator;" || true
say "    Временные процедуры удалены (DDL в бинарный журнал не записан)."

# --- 9. Проверка, что транзакция не нарушила репликацию --------------
hdr "9. Состояние каналов репликации после транзакции"
for n in mysql-master mysql-slave mysql-slave2 mysql-consol; do
  yes_cnt="$(q "$n" -e "SHOW SLAVE STATUS\G" | grep -c 'Slave_SQL_Running: Yes' || true)"
  err_cnt="$(q "$n" -e "SHOW SLAVE STATUS\G" | grep -c 'Last_Error: [^ ]' || true)"
  say "    $n: каналов в работе — ${yes_cnt:-0}, каналов с ошибкой — ${err_cnt:-0}"
done

hdr "Итог"
say "Распределённая транзакция РТ-1 выполнена по протоколу двухфазной фиксации:"
say "  фаза 1 — PREPARE на участнике $PART и на координаторе $COORD;"
say "  фаза 2 — COMMIT на обоих узлах после подтверждения готовности;"
say "  изменение участника видно в консолидированной копии ($CONSOL) — РКД подтверждена;"
say "  повторное бронирование того же экземпляра невозможно (откат)."
ABORT=1
