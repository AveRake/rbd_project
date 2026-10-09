-- =====================================================================
--  CampusRent — файл 06: индексы для повышения эффективности запросов
--  Индексы по внешним ключам InnoDB создаёт автоматически; здесь
--  добавлены составные и дополнительные индексы под конкретные запросы.
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

-- Техника: поиск свободных экземпляров заданной модели / загрузка филиала
CREATE INDEX idx_eq_status_model ON equipment_units (EQ_STATUS, EQ_MOD);
CREATE INDEX idx_eq_branch_status ON equipment_units (EQ_BR, EQ_STATUS);

-- Заявки: отбор по филиалу и статусу, поиск по периодам
CREATE INDEX idx_req_branch_status ON requests (REQ_BR, REQ_STATUS);
CREATE INDEX idx_req_period       ON requests (REQ_BEGIN, REQ_END);
CREATE INDEX idx_req_created      ON requests (REQ_CREATED);

-- Позиции заявок: подбор под модель
CREATE INDEX idx_rit_model ON request_items (RIT_MOD);
CREATE INDEX idx_rit_period ON request_items (RIT_BEGIN, RIT_END);

-- Выдачи: поиск занятости экземпляра и просроченных возвратов
CREATE INDEX idx_rnt_eq_period ON rentals (RNT_EQ, RNT_ISSUE, RNT_DUE);
CREATE INDEX idx_rnt_return    ON rentals (RNT_RETURN);

-- Финансы
CREATE INDEX idx_pay_date ON payments (PAY_DATE);

-- Клиенты
CREATE INDEX idx_un_city ON universities (UN_CITY);

-- Обслуживание
CREATE INDEX idx_mnt_eq_type ON maintenance (MNT_EQ, MNT_TYPE);

-- Тарифы
CREATE INDEX idx_tar_mod_unit ON tariffs (TAR_MOD, TAR_UNIT);

-- Номенклатура
CREATE INDEX idx_models_cat ON models (MOD_CAT);
