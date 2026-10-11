-- =====================================================================
--  CampusRent — файл 06: индексы для повышения эффективности запросов
--
--  Индексы по внешним ключам InnoDB создаёт автоматически; здесь
--  добавлены составные и дополнительные индексы под конкретные запросы.
--
--  Файл ИДЕМПОТЕНТЕН: повторный запуск не приводит к ошибке 1061
--  (Duplicate key name). В MySQL 8.0 нет синтаксиса
--  CREATE INDEX IF NOT EXISTS, поэтому каждый индекс создаётся
--  динамическим SQL внутри вспомогательной процедуры, которая сначала
--  проверяет наличие индекса в information_schema.statistics.
--  В конце процедура удаляется, чтобы не оставалась в схеме.
--
--  ВНИМАНИЕ. Идемпотентность действует в пределах одного узла.
--  В MySQL 8.0 параметр log_replica_updates включён по умолчанию,
--  поэтому DDL-команды этого файла попадают в бинарный журнал узла
--  и разносятся по каналам репликации. Если запустить файл повторно
--  на ОДНОМ узле работающего стенда, вспомогательная процедура
--  «размножится» по каналам, и узел, где такой объект уже есть,
--  остановит канал с ошибкой 1304 «... already exists».
--  Поэтому DDL выполняется один раз на всех узлах до включения
--  репликации (см. replication/setup.sh, шаг 3).
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS create_index_if_missing;

DELIMITER $$
CREATE PROCEDURE create_index_if_missing(
  IN p_table VARCHAR(64),
  IN p_index VARCHAR(64),
  IN p_ddl   TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name   = p_table
      AND index_name   = p_index
  ) THEN
    SET @ddl = p_ddl;
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  ELSE
    SELECT CONCAT('индекс ', p_index, ' уже существует — пропущен') AS note;
  END IF;
END$$
DELIMITER ;

-- Техника: поиск свободных экземпляров заданной модели / загрузка филиала
CALL create_index_if_missing('equipment_units', 'idx_eq_status_model',
  'CREATE INDEX idx_eq_status_model ON equipment_units (EQ_STATUS, EQ_MOD)');
CALL create_index_if_missing('equipment_units', 'idx_eq_branch_status',
  'CREATE INDEX idx_eq_branch_status ON equipment_units (EQ_BR, EQ_STATUS)');

-- Заявки: отбор по филиалу и статусу, поиск по периодам
CALL create_index_if_missing('requests', 'idx_req_branch_status',
  'CREATE INDEX idx_req_branch_status ON requests (REQ_BR, REQ_STATUS)');
CALL create_index_if_missing('requests', 'idx_req_period',
  'CREATE INDEX idx_req_period ON requests (REQ_BEGIN, REQ_END)');
CALL create_index_if_missing('requests', 'idx_req_created',
  'CREATE INDEX idx_req_created ON requests (REQ_CREATED)');

-- Позиции заявок: подбор под модель
CALL create_index_if_missing('request_items', 'idx_rit_model',
  'CREATE INDEX idx_rit_model ON request_items (RIT_MOD)');
CALL create_index_if_missing('request_items', 'idx_rit_period',
  'CREATE INDEX idx_rit_period ON request_items (RIT_BEGIN, RIT_END)');

-- Выдачи: поиск занятости экземпляра и просроченные возвраты
CALL create_index_if_missing('rentals', 'idx_rnt_eq_period',
  'CREATE INDEX idx_rnt_eq_period ON rentals (RNT_EQ, RNT_ISSUE, RNT_DUE)');
CALL create_index_if_missing('rentals', 'idx_rnt_return',
  'CREATE INDEX idx_rnt_return ON rentals (RNT_RETURN)');

-- Финансы
CALL create_index_if_missing('payments', 'idx_pay_date',
  'CREATE INDEX idx_pay_date ON payments (PAY_DATE)');

-- Клиенты
CALL create_index_if_missing('universities', 'idx_un_city',
  'CREATE INDEX idx_un_city ON universities (UN_CITY)');

-- Обслуживание
CALL create_index_if_missing('maintenance', 'idx_mnt_eq_type',
  'CREATE INDEX idx_mnt_eq_type ON maintenance (MNT_EQ, MNT_TYPE)');

-- Тарифы
CALL create_index_if_missing('tariffs', 'idx_tar_mod_unit',
  'CREATE INDEX idx_tar_mod_unit ON tariffs (TAR_MOD, TAR_UNIT)');

-- Номенклатура
CALL create_index_if_missing('models', 'idx_models_cat',
  'CREATE INDEX idx_models_cat ON models (MOD_CAT)');

DROP PROCEDURE create_index_if_missing;

-- Примечание. Четыре индекса частично дублируют автоматически
-- созданные индексы InnoDB по внешним ключам и уникальным ключам:
--   idx_models_cat    ~ автоиндекс FK models(MOD_CAT);
--   idx_rit_model     ~ автоиндекс FK request_items(RIT_MOD);
--   idx_tar_mod_unit  ~ левый префикс uniq_tar(TAR_MOD, TAR_UNIT, TAR_BEGIN);
--   idx_rnt_eq_period ~ почти покрыт uniq_rnt(RNT_EQ, RNT_ISSUE) + RNT_DUE.
-- Они оставлены сознательно: на учебных объёмах (сотни–тысячи строк)
-- накладные расходы незаметны, а состав индексов соответствует
-- перечню часто используемых условий отбора в отчётных запросах.
-- При переходе на промышленные объёмы эти четыре индекса можно снять.
