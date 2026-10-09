#!/usr/bin/env bash
# =====================================================================
#  CampusRent — развёртывание стенда репликации (MySQL 8.0 в Docker).
#
#  Что делает скрипт:
#    1) поднимает 4 контейнера;
#    2) загружает ОДИНАКОВЫЙ снимок схемы и данных во все узлы;
#    3) фиксирует текущие позиции бинарных журналов;
#    4) включает репликацию:
#         РОК  — ЦО -> филиалы (справочники)
#         РБОК — филиал СПб -> ЦО (таблицы клиентов)
#         РКД  — ЦО и филиал -> узел консолидации
#    5) печатает состояние каналов.
#
#  Почему позиции фиксируются заранее: репликация должна начаться
#  с текущего момента. Если запустить её «с начала журнала», филиал
#  повторно применит уже загруженные данные и упадёт на дубликатах.
#
#  Запуск:              bash setup.sh
#  Повторный запуск:    docker compose down -v && bash setup.sh
# =====================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MY="mysql -uroot -ppassword --default-character-set=utf8mb4"
SQL_FILES="01_schema.sql 02_reference_data.sql 03_test_data.sql 04_views.sql 05_triggers.sql 06_indexes.sql 07_users_grants.sql"

q()   { docker exec "$1" $MY "${@:2}"; }   # выполнить запрос на узле
qin() { docker exec -i "$1" $MY; }         # подать SQL на stdin

echo "==> 1/5 Запуск контейнеров"
docker compose up -d

echo "==> 2/5 Ожидание готовности узлов"
for svc in mysql-master mysql-slave mysql-slave2 mysql-consol; do
  printf "    %-14s" "$svc"
  ready=0
  for _ in $(seq 1 60); do
    if docker exec "$svc" mysqladmin ping -uroot -ppassword --silent >/dev/null 2>&1; then
      ready=1; break
    fi
    printf "."; sleep 2
  done
  if [ "$ready" = 1 ]; then echo " готов"; else echo " НЕ ЗАПУСТИЛСЯ"; exit 1; fi
done

echo "==> 3/5 Загрузка схемы и данных во все узлы (одинаковый снимок)"
for svc in mysql-master mysql-slave mysql-slave2 mysql-consol; do
  echo "    -> $svc"
  for f in $SQL_FILES; do
    qin "$svc" < "$ROOT/sql/$f"
  done
done

echo "==> 4/5 Фиксация позиций бинарных журналов"
M_POS_RAW="$(q mysql-master -N -e 'SHOW MASTER STATUS' | awk '{print $1" "$2}')"
S_POS_RAW="$(q mysql-slave  -N -e 'SHOW MASTER STATUS' | awk '{print $1" "$2}')"
M_FILE="${M_POS_RAW% *}"; M_OFF="${M_POS_RAW#* }"
S_FILE="${S_POS_RAW% *}"; S_OFF="${S_POS_RAW#* }"
if [ -z "$M_FILE" ] || [ -z "$S_FILE" ]; then
  echo "    Не удалось прочитать позицию журнала. Проверьте log-bin в конфигурации узла."
  exit 1
fi
echo "    ЦО:     $M_FILE:$M_OFF"
echo "    Филиал: $S_FILE:$S_OFF"

echo "==> 5/5 Настройка репликации"

# сброс ранее настроенных каналов (если скрипт запускают повторно)
docker exec mysql-master  mysql -uroot -ppassword -e "STOP SLAVE"        >/dev/null 2>&1 || true
docker exec mysql-master  mysql -uroot -ppassword -e "RESET SLAVE ALL"   >/dev/null 2>&1 || true
for svc in mysql-slave mysql-slave2; do
  docker exec "$svc" mysql -uroot -ppassword -e "STOP SLAVE"      >/dev/null 2>&1 || true
  docker exec "$svc" mysql -uroot -ppassword -e "RESET SLAVE ALL" >/dev/null 2>&1 || true
done
for ch in hq spb; do
  docker exec mysql-consol mysql -uroot -ppassword -e "STOP SLAVE FOR CHANNEL '$ch'"      >/dev/null 2>&1 || true
  docker exec mysql-consol mysql -uroot -ppassword -e "RESET SLAVE ALL FOR CHANNEL '$ch'" >/dev/null 2>&1 || true
done

# РОК: ЦО -> филиалы
for svc in mysql-slave mysql-slave2; do
  echo "    РОК: mysql-master -> $svc"
  qin "$svc" <<SQL
CHANGE MASTER TO
  MASTER_HOST='mysql-master', MASTER_USER='repl', MASTER_PASSWORD='password',
  MASTER_LOG_FILE='$M_FILE', MASTER_LOG_POS=$M_OFF, GET_MASTER_PUBLIC_KEY=1;
START SLAVE;
SQL
done

# РБОК: филиал СПб -> ЦО (перечень таблиц задан в master.cnf)
echo "    РБОК: mysql-slave -> mysql-master"
qin mysql-master <<SQL
CHANGE MASTER TO
  MASTER_HOST='mysql-slave', MASTER_USER='replslave', MASTER_PASSWORD='password',
  MASTER_LOG_FILE='$S_FILE', MASTER_LOG_POS=$S_OFF, GET_MASTER_PUBLIC_KEY=1;
START SLAVE;
SQL

# РКД: ЦО и филиал -> узел консолидации
echo "    РКД: mysql-master и mysql-slave -> mysql-consol"
qin mysql-consol <<SQL
CHANGE MASTER TO MASTER_HOST='mysql-master', MASTER_USER='repl', MASTER_PASSWORD='password',
  MASTER_LOG_FILE='$M_FILE', MASTER_LOG_POS=$M_OFF, GET_MASTER_PUBLIC_KEY=1 FOR CHANNEL 'hq';
CHANGE MASTER TO MASTER_HOST='mysql-slave', MASTER_USER='replslave', MASTER_PASSWORD='password',
  MASTER_LOG_FILE='$S_FILE', MASTER_LOG_POS=$S_OFF, GET_MASTER_PUBLIC_KEY=1 FOR CHANNEL 'spb';
START SLAVE FOR CHANNEL 'hq';
START SLAVE FOR CHANNEL 'spb';
SQL

echo
echo "==> Состояние каналов"
sleep 4
for svc in mysql-slave mysql-master mysql-consol; do
  echo "--- $svc"
  q "$svc" -e "SHOW SLAVE STATUS\G" \
    | grep -E "Channel_Name|Master_Host|Slave_IO_Running|Slave_SQL_Running|Last_Error" || true
done
echo
echo "Ожидается Slave_IO_Running: Yes и Slave_SQL_Running: Yes."
echo "Если Last_Error не пуст — пришлите вывод, разберёмся."
