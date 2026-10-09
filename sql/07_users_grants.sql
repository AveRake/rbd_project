-- =====================================================================
--  CampusRent — файл 07: роли, пользователи и права доступа
--  Примечание: полный перечень команд приведён для проекта БД;
--  в отчёте достаточно привести 3-5 примеров (см. методические указания).
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- 1. Роли СУБД
-- ---------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS 'role_br_manager';
CREATE ROLE IF NOT EXISTS 'role_storekeeper';
CREATE ROLE IF NOT EXISTS 'role_service';
CREATE ROLE IF NOT EXISTS 'role_br_head';
CREATE ROLE IF NOT EXISTS 'role_univ_rep';
CREATE ROLE IF NOT EXISTS 'role_hq_spec';
CREATE ROLE IF NOT EXISTS 'role_hq_boss';
CREATE ROLE IF NOT EXISTS 'role_accountant';

-- ---------------------------------------------------------------------
-- 2. Права ролей на таблицы
-- ---------------------------------------------------------------------

-- Менеджер филиала
GRANT SELECT ON campusrent.branches            TO 'role_br_manager';
GRANT SELECT ON campusrent.categories          TO 'role_br_manager';
GRANT SELECT ON campusrent.models              TO 'role_br_manager';
GRANT SELECT ON campusrent.model_components    TO 'role_br_manager';
GRANT SELECT ON campusrent.model_purposes      TO 'role_br_manager';
GRANT SELECT ON campusrent.tariffs             TO 'role_br_manager';
GRANT SELECT ON campusrent.condition_grades    TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.universities    TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.departments     TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.representatives TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.equipment_units TO 'role_br_manager';
GRANT SELECT, INSERT ON campusrent.transfers   TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.requests      TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.request_items TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.contracts     TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.rentals       TO 'role_br_manager';
GRANT SELECT, INSERT, UPDATE ON campusrent.payments      TO 'role_br_manager';
GRANT SELECT ON campusrent.maintenance         TO 'role_br_manager';
GRANT SELECT ON campusrent.employees           TO 'role_br_manager';

-- Сотрудник склада
GRANT SELECT ON campusrent.models           TO 'role_storekeeper';
GRANT SELECT ON campusrent.condition_grades TO 'role_storekeeper';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.equipment_units TO 'role_storekeeper';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.transfers       TO 'role_storekeeper';
GRANT SELECT, INSERT ON campusrent.maintenance TO 'role_storekeeper';
GRANT SELECT ON campusrent.branches         TO 'role_storekeeper';
GRANT SELECT ON campusrent.requests         TO 'role_storekeeper';
GRANT SELECT ON campusrent.contracts        TO 'role_storekeeper';
GRANT SELECT ON campusrent.rentals          TO 'role_storekeeper';

-- Специалист сервисного центра
GRANT SELECT ON campusrent.equipment_units    TO 'role_service';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.maintenance TO 'role_service';
GRANT SELECT, UPDATE ON campusrent.equipment_units TO 'role_service';
GRANT SELECT ON campusrent.maintenance_types  TO 'role_service';
GRANT SELECT ON campusrent.condition_grades   TO 'role_service';

-- Руководитель филиала (чтение + отчёты)
GRANT SELECT ON campusrent.* TO 'role_br_head';

-- Представитель вуза (только свои заявки и договоры через представления)
GRANT SELECT ON campusrent.models            TO 'role_univ_rep';
GRANT SELECT ON campusrent.categories        TO 'role_univ_rep';
GRANT SELECT ON campusrent.tariffs           TO 'role_univ_rep';
GRANT SELECT ON campusrent.v_my_university_requests  TO 'role_univ_rep';
GRANT SELECT ON campusrent.v_my_university_contracts TO 'role_univ_rep';
GRANT SELECT ON campusrent.v_available_equipment     TO 'role_univ_rep';

-- Сотрудник центрального офиса (номенклатура и справочники)
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.categories        TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.models            TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.model_components  TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.model_purposes    TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.tariffs           TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.branches          TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.employees         TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.request_statuses  TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.payment_methods   TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.maintenance_types TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.condition_grades  TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.universities      TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.departments       TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.representatives   TO 'role_hq_spec';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.equipment_units   TO 'role_hq_spec';
GRANT SELECT ON campusrent.v_consolidated_fleet TO 'role_hq_spec';

-- Руководство ЦО (чтение всей БД и сводные представления)
GRANT SELECT ON campusrent.* TO 'role_hq_boss';

-- Бухгалтерия
GRANT SELECT ON campusrent.contracts  TO 'role_accountant';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusrent.payments TO 'role_accountant';
GRANT SELECT ON campusrent.universities  TO 'role_accountant';
GRANT SELECT ON campusrent.branches      TO 'role_accountant';
GRANT SELECT ON campusrent.rentals       TO 'role_accountant';
GRANT SELECT ON campusrent.payment_methods TO 'role_accountant';

-- ---------------------------------------------------------------------
-- 3. Учётные записи сотрудников и представителей
-- ---------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'hq_boss'@'%'      IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'hq_spec'@'%'      IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'accountant'@'%'   IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'spb_head'@'%'     IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'spb_manager'@'%'  IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'spb_store'@'%'    IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'kzn_manager'@'%'  IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'nsk_service'@'%'  IDENTIFIED BY 'CampusRent#2026';

GRANT 'role_hq_boss'    TO 'hq_boss'@'%';
GRANT 'role_hq_spec'    TO 'hq_spec'@'%';
GRANT 'role_accountant' TO 'accountant'@'%';
GRANT 'role_br_head'    TO 'spb_head'@'%';
GRANT 'role_br_manager' TO 'spb_manager'@'%';
GRANT 'role_storekeeper' TO 'spb_store'@'%';
GRANT 'role_br_manager' TO 'kzn_manager'@'%';
GRANT 'role_service'    TO 'nsk_service'@'%';

SET DEFAULT ROLE ALL TO
  'hq_boss'@'%', 'hq_spec'@'%', 'accountant'@'%', 'spb_head'@'%',
  'spb_manager'@'%', 'spb_store'@'%', 'kzn_manager'@'%', 'nsk_service'@'%';

-- Представители нескольких вузов (логин вида univ_<UN_ID>)
CREATE USER IF NOT EXISTS 'univ_1001'@'%' IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'univ_1002'@'%' IDENTIFIED BY 'CampusRent#2026';
CREATE USER IF NOT EXISTS 'univ_1013'@'%' IDENTIFIED BY 'CampusRent#2026';

GRANT 'role_univ_rep' TO 'univ_1001'@'%', 'univ_1002'@'%', 'univ_1013'@'%';
SET DEFAULT ROLE ALL TO 'univ_1001'@'%', 'univ_1002'@'%', 'univ_1013'@'%';

-- ---------------------------------------------------------------------
-- 4. Пользователь для репликации
-- ---------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'repl'@'%' IDENTIFIED BY 'password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';

FLUSH PRIVILEGES;

-- =====================================================================
--  Роли, пользователи и права доступа созданы.
-- =====================================================================
