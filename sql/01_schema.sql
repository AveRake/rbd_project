-- =====================================================================
--  CampusRent — распределённая БД сервиса аренды техники для вузов
--  Файл 01: создание базы данных и таблиц (DDL)
--  СУБД: MySQL 8.0  (InnoDB, utf8mb4)
--  Всего отношений: 22
-- =====================================================================

CREATE DATABASE IF NOT EXISTS campusrent
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE campusrent;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS maintenance;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS rentals;
DROP TABLE IF EXISTS contracts;
DROP TABLE IF EXISTS request_items;
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS transfers;
DROP TABLE IF EXISTS equipment_units;
DROP TABLE IF EXISTS representatives;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS universities;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS condition_grades;
DROP TABLE IF EXISTS maintenance_types;
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS request_statuses;
DROP TABLE IF EXISTS tariffs;
DROP TABLE IF EXISTS model_purposes;
DROP TABLE IF EXISTS model_components;
DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS branches;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. ФИЛИАЛЫ (Branches) — справочная таблица, узел сети
-- ---------------------------------------------------------------------
CREATE TABLE branches (
  BR_ID      VARCHAR(8)   NOT NULL,
  BR_NAME    VARCHAR(100) NOT NULL,
  BR_CITY    VARCHAR(50)  NOT NULL,
  BR_ADDRESS VARCHAR(150) NOT NULL,
  BR_PHONE   VARCHAR(20),
  BR_EMAIL   VARCHAR(50),
  BR_MANAGER VARCHAR(100),
  BR_BEGIN   DATE         NOT NULL,
  BR_END     DATE,
  PRIMARY KEY (BR_ID),
  CONSTRAINT chk_br_period CHECK (BR_END IS NULL OR BR_END > BR_BEGIN)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. КАТЕГОРИИ ТЕХНИКИ (Categories)
-- ---------------------------------------------------------------------
CREATE TABLE categories (
  CAT_ID    NUMERIC(3)  NOT NULL,
  CAT_NAME  VARCHAR(60) NOT NULL,
  CAT_DESCR VARCHAR(200),
  PRIMARY KEY (CAT_ID),
  CONSTRAINT uniq_cat_name UNIQUE (CAT_NAME)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. МОДЕЛИ ТЕХНИКИ (Models) — номенклатура
-- ---------------------------------------------------------------------
CREATE TABLE models (
  MOD_ID    NUMERIC(6)    NOT NULL,
  MOD_CAT   NUMERIC(3)    NOT NULL,
  MOD_BRAND VARCHAR(40)   NOT NULL,
  MOD_NAME  VARCHAR(80)   NOT NULL,
  MOD_DESCR VARCHAR(300),
  MOD_COST  NUMERIC(12,2) NOT NULL,
  MOD_MINQTY NUMERIC(3)   NOT NULL DEFAULT 1,
  PRIMARY KEY (MOD_ID),
  CONSTRAINT uniq_mod UNIQUE (MOD_BRAND, MOD_NAME),
  CONSTRAINT chk_mod_cost CHECK (MOD_COST > 0),
  CONSTRAINT chk_mod_minqty CHECK (MOD_MINQTY > 0),
  CONSTRAINT fk_mod_cat FOREIGN KEY (MOD_CAT) REFERENCES categories(CAT_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. КОМПЛЕКТАЦИЯ МОДЕЛИ (Model_components) — результат 1НФ/4НФ
-- ---------------------------------------------------------------------
CREATE TABLE model_components (
  MC_ID   BIGINT      NOT NULL AUTO_INCREMENT,
  MC_MOD  NUMERIC(6)  NOT NULL,
  MC_ITEM VARCHAR(80) NOT NULL,
  MC_QTY  NUMERIC(3)  NOT NULL DEFAULT 1,
  PRIMARY KEY (MC_ID),
  CONSTRAINT uniq_mc UNIQUE (MC_MOD, MC_ITEM),
  CONSTRAINT chk_mc_qty CHECK (MC_QTY > 0),
  CONSTRAINT fk_mc_mod FOREIGN KEY (MC_MOD) REFERENCES models(MOD_ID)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. НАЗНАЧЕНИЕ МОДЕЛИ (Model_purposes)
-- ---------------------------------------------------------------------
CREATE TABLE model_purposes (
  MP_ID      BIGINT      NOT NULL AUTO_INCREMENT,
  MP_MOD     NUMERIC(6)  NOT NULL,
  MP_PURPOSE VARCHAR(60) NOT NULL,
  PRIMARY KEY (MP_ID),
  CONSTRAINT uniq_mp UNIQUE (MP_MOD, MP_PURPOSE),
  CONSTRAINT fk_mp_mod FOREIGN KEY (MP_MOD) REFERENCES models(MOD_ID)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. ТАРИФЫ (Tariffs) — справочник с периодом актуальности
-- ---------------------------------------------------------------------
CREATE TABLE tariffs (
  TAR_ID      NUMERIC(6)    NOT NULL,
  TAR_MOD     NUMERIC(6)    NOT NULL,
  TAR_UNIT    VARCHAR(10)   NOT NULL,
  TAR_PRICE   NUMERIC(10,2) NOT NULL,
  TAR_DEPOSIT NUMERIC(12,2) NOT NULL DEFAULT 0,
  TAR_BEGIN   DATE          NOT NULL,
  TAR_END     DATE,
  PRIMARY KEY (TAR_ID),
  CONSTRAINT uniq_tar UNIQUE (TAR_MOD, TAR_UNIT, TAR_BEGIN),
  CONSTRAINT chk_tar_unit CHECK (TAR_UNIT IN ('день','неделя','месяц')),
  CONSTRAINT chk_tar_price CHECK (TAR_PRICE > 0),
  CONSTRAINT chk_tar_deposit CHECK (TAR_DEPOSIT >= 0),
  CONSTRAINT chk_tar_period CHECK (TAR_END IS NULL OR TAR_END > TAR_BEGIN),
  CONSTRAINT fk_tar_mod FOREIGN KEY (TAR_MOD) REFERENCES models(MOD_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 7. СТАТУСЫ ЗАЯВОК (Request_statuses)
-- ---------------------------------------------------------------------
CREATE TABLE request_statuses (
  RST_ID   NUMERIC(2)  NOT NULL,
  RST_NAME VARCHAR(30) NOT NULL,
  PRIMARY KEY (RST_ID),
  CONSTRAINT uniq_rst_name UNIQUE (RST_NAME)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 8. СПОСОБЫ ОПЛАТЫ (Payment_methods)
-- ---------------------------------------------------------------------
CREATE TABLE payment_methods (
  PM_ID   NUMERIC(2)  NOT NULL,
  PM_NAME VARCHAR(30) NOT NULL,
  PRIMARY KEY (PM_ID),
  CONSTRAINT uniq_pm_name UNIQUE (PM_NAME)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 9. ВИДЫ ОБСЛУЖИВАНИЯ (Maintenance_types)
-- ---------------------------------------------------------------------
CREATE TABLE maintenance_types (
  MT_ID   NUMERIC(2)  NOT NULL,
  MT_NAME VARCHAR(40) NOT NULL,
  PRIMARY KEY (MT_ID),
  CONSTRAINT uniq_mt_name UNIQUE (MT_NAME)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 10. СТЕПЕНИ СОСТОЯНИЯ (Condition_grades)
-- ---------------------------------------------------------------------
CREATE TABLE condition_grades (
  CG_ID   NUMERIC(2)  NOT NULL,
  CG_NAME VARCHAR(30) NOT NULL,
  PRIMARY KEY (CG_ID),
  CONSTRAINT uniq_cg_name UNIQUE (CG_NAME)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 11. СОТРУДНИКИ (Employees)
-- ---------------------------------------------------------------------
CREATE TABLE employees (
  EMP_ID       NUMERIC(6)   NOT NULL,
  EMP_BR       VARCHAR(8)   NOT NULL,
  EMP_FIO      VARCHAR(100) NOT NULL,
  EMP_POSITION VARCHAR(60)  NOT NULL,
  EMP_PHONE    VARCHAR(20),
  EMP_EMAIL    VARCHAR(50),
  EMP_LOGIN    VARCHAR(30)  NOT NULL,
  PRIMARY KEY (EMP_ID),
  CONSTRAINT uniq_emp_login UNIQUE (EMP_LOGIN),
  CONSTRAINT fk_emp_br FOREIGN KEY (EMP_BR) REFERENCES branches(BR_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 12. ВУЗЫ (Universities)
-- ---------------------------------------------------------------------
CREATE TABLE universities (
  UN_ID      NUMERIC(6)   NOT NULL,
  UN_NAME    VARCHAR(150) NOT NULL,
  UN_SHORT   VARCHAR(60)  NOT NULL,
  UN_INN     CHAR(10)     NOT NULL,
  UN_KPP     CHAR(9),
  UN_ADDRESS VARCHAR(150) NOT NULL,
  UN_CITY    VARCHAR(50)  NOT NULL,
  UN_PHONE   VARCHAR(20),
  UN_EMAIL   VARCHAR(50),
  UN_BR      VARCHAR(8)   NOT NULL,
  PRIMARY KEY (UN_ID),
  CONSTRAINT uniq_un_short UNIQUE (UN_SHORT),
  CONSTRAINT uniq_un_inn   UNIQUE (UN_INN),
  CONSTRAINT fk_un_br FOREIGN KEY (UN_BR) REFERENCES branches(BR_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 13. ПОДРАЗДЕЛЕНИЯ ВУЗА (Departments)
-- ---------------------------------------------------------------------
CREATE TABLE departments (
  DEP_ID    NUMERIC(6)   NOT NULL,
  DEP_UN    NUMERIC(6)   NOT NULL,
  DEP_NAME  VARCHAR(100) NOT NULL,
  DEP_HEAD  VARCHAR(100),
  DEP_PHONE VARCHAR(20),
  DEP_EMAIL VARCHAR(50),
  PRIMARY KEY (DEP_ID),
  CONSTRAINT uniq_dep UNIQUE (DEP_UN, DEP_NAME),
  CONSTRAINT fk_dep_un FOREIGN KEY (DEP_UN) REFERENCES universities(UN_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 14. ПРЕДСТАВИТЕЛИ ВУЗОВ (Representatives)
-- ---------------------------------------------------------------------
CREATE TABLE representatives (
  REP_ID       NUMERIC(6)   NOT NULL,
  REP_UN       NUMERIC(6)   NOT NULL,
  REP_DEP      NUMERIC(6),
  REP_FIO      VARCHAR(100) NOT NULL,
  REP_POSITION VARCHAR(60)  NOT NULL,
  REP_PHONE    VARCHAR(20)  NOT NULL,
  REP_EMAIL    VARCHAR(50),
  REP_PASSPORT CHAR(10),
  PRIMARY KEY (REP_ID),
  CONSTRAINT uniq_rep_passport UNIQUE (REP_PASSPORT),
  CONSTRAINT fk_rep_un  FOREIGN KEY (REP_UN)  REFERENCES universities(UN_ID),
  CONSTRAINT fk_rep_dep FOREIGN KEY (REP_DEP) REFERENCES departments(DEP_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 15. ЭКЗЕМПЛЯРЫ ТЕХНИКИ (Equipment_units) — фрагментируется по филиалам
-- ---------------------------------------------------------------------
CREATE TABLE equipment_units (
  EQ_ID       NUMERIC(10) NOT NULL,
  EQ_INV      CHAR(12)    NOT NULL,
  EQ_MOD      NUMERIC(6)  NOT NULL,
  EQ_BR       VARCHAR(8)  NOT NULL,
  EQ_STATUS   VARCHAR(12) NOT NULL DEFAULT 'свободна',
  EQ_COND     NUMERIC(2)  NOT NULL,
  EQ_ACQUIRE  DATE        NOT NULL,
  EQ_LOCATION VARCHAR(60),
  EQ_NOTE     VARCHAR(200),
  PRIMARY KEY (EQ_ID),
  CONSTRAINT uniq_eq_inv UNIQUE (EQ_INV),
  CONSTRAINT chk_eq_status CHECK
    (EQ_STATUS IN ('свободна','аренда','бронь','обслуживание','списана')),
  CONSTRAINT fk_eq_mod FOREIGN KEY (EQ_MOD) REFERENCES models(MOD_ID),
  CONSTRAINT fk_eq_br  FOREIGN KEY (EQ_BR)  REFERENCES branches(BR_ID),
  CONSTRAINT fk_eq_cond FOREIGN KEY (EQ_COND) REFERENCES condition_grades(CG_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 16. ПЕРЕМЕЩЕНИЯ ТЕХНИКИ (Transfers)
-- ---------------------------------------------------------------------
CREATE TABLE transfers (
  TR_ID     NUMERIC(10)  NOT NULL,
  TR_EQ     NUMERIC(10)  NOT NULL,
  TR_FROM   VARCHAR(8)   NOT NULL,
  TR_TO     VARCHAR(8)   NOT NULL,
  TR_DATE   DATE         NOT NULL,
  TR_REASON VARCHAR(200),
  TR_DOC    VARCHAR(30),
  PRIMARY KEY (TR_ID),
  CONSTRAINT chk_tr_diff CHECK (TR_FROM <> TR_TO),
  CONSTRAINT fk_tr_eq   FOREIGN KEY (TR_EQ)   REFERENCES equipment_units(EQ_ID),
  CONSTRAINT fk_tr_from FOREIGN KEY (TR_FROM) REFERENCES branches(BR_ID),
  CONSTRAINT fk_tr_to   FOREIGN KEY (TR_TO)   REFERENCES branches(BR_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 17. ЗАЯВКИ (Requests)
-- ---------------------------------------------------------------------
CREATE TABLE requests (
  REQ_ID      NUMERIC(10)   NOT NULL,
  REQ_NUMBER  CHAR(12)      NOT NULL,
  REQ_UN      NUMERIC(6)    NOT NULL,
  REQ_DEP     NUMERIC(6)    NOT NULL,
  REQ_REP     NUMERIC(6)    NOT NULL,
  REQ_BR      VARCHAR(8)    NOT NULL,
  REQ_CREATED DATE          NOT NULL,
  REQ_BEGIN   DATE          NOT NULL,
  REQ_END     DATE          NOT NULL,
  REQ_STATUS  NUMERIC(2)    NOT NULL,
  REQ_SUM     NUMERIC(12,2) NOT NULL DEFAULT 0,
  REQ_COMMENT VARCHAR(300),
  PRIMARY KEY (REQ_ID),
  CONSTRAINT uniq_req_number UNIQUE (REQ_NUMBER),
  CONSTRAINT chk_req_period CHECK (REQ_END > REQ_BEGIN),
  CONSTRAINT chk_req_sum CHECK (REQ_SUM >= 0),
  CONSTRAINT fk_req_un  FOREIGN KEY (REQ_UN)  REFERENCES universities(UN_ID),
  CONSTRAINT fk_req_dep FOREIGN KEY (REQ_DEP) REFERENCES departments(DEP_ID),
  CONSTRAINT fk_req_rep FOREIGN KEY (REQ_REP) REFERENCES representatives(REP_ID),
  CONSTRAINT fk_req_br  FOREIGN KEY (REQ_BR)  REFERENCES branches(BR_ID),
  CONSTRAINT fk_req_status FOREIGN KEY (REQ_STATUS) REFERENCES request_statuses(RST_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 18. ПОЗИЦИИ ЗАЯВКИ (Request_items)
-- ---------------------------------------------------------------------
CREATE TABLE request_items (
  RIT_ID    NUMERIC(10)   NOT NULL,
  RIT_REQ   NUMERIC(10)   NOT NULL,
  RIT_MOD   NUMERIC(6)    NOT NULL,
  RIT_QTY   NUMERIC(3)    NOT NULL,
  RIT_BEGIN DATE          NOT NULL,
  RIT_END   DATE          NOT NULL,
  RIT_TAR   NUMERIC(6)    NOT NULL,
  RIT_COST  NUMERIC(12,2) NOT NULL,
  PRIMARY KEY (RIT_ID),
  CONSTRAINT uniq_rit UNIQUE (RIT_REQ, RIT_MOD, RIT_BEGIN),
  CONSTRAINT chk_rit_qty CHECK (RIT_QTY > 0),
  CONSTRAINT chk_rit_period CHECK (RIT_END > RIT_BEGIN),
  CONSTRAINT chk_rit_cost CHECK (RIT_COST >= 0),
  CONSTRAINT fk_rit_req FOREIGN KEY (RIT_REQ) REFERENCES requests(REQ_ID)
    ON DELETE CASCADE,
  CONSTRAINT fk_rit_mod FOREIGN KEY (RIT_MOD) REFERENCES models(MOD_ID),
  CONSTRAINT fk_rit_tar FOREIGN KEY (RIT_TAR) REFERENCES tariffs(TAR_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 19. ДОГОВОРЫ (Contracts)
-- ---------------------------------------------------------------------
CREATE TABLE contracts (
  CTR_ID      NUMERIC(10)   NOT NULL,
  CTR_NUMBER  CHAR(15)      NOT NULL,
  CTR_REQ     NUMERIC(10)   NOT NULL,
  CTR_SIGN    DATE          NOT NULL,
  CTR_BEGIN   DATE          NOT NULL,
  CTR_END     DATE          NOT NULL,
  CTR_SUM     NUMERIC(12,2) NOT NULL,
  CTR_DEPOSIT NUMERIC(12,2) NOT NULL DEFAULT 0,
  CTR_STATUS  VARCHAR(12)   NOT NULL DEFAULT 'действует',
  PRIMARY KEY (CTR_ID),
  CONSTRAINT uniq_ctr_number UNIQUE (CTR_NUMBER),
  CONSTRAINT uniq_ctr_req    UNIQUE (CTR_REQ),
  CONSTRAINT chk_ctr_period CHECK (CTR_END > CTR_BEGIN),
  CONSTRAINT chk_ctr_sum CHECK (CTR_SUM > 0),
  CONSTRAINT chk_ctr_deposit CHECK (CTR_DEPOSIT >= 0),
  CONSTRAINT chk_ctr_status CHECK (CTR_STATUS IN ('действует','закрыт','расторгнут')),
  CONSTRAINT fk_ctr_req FOREIGN KEY (CTR_REQ) REFERENCES requests(REQ_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 20. ВЫДАЧИ (Rentals)
-- ---------------------------------------------------------------------
CREATE TABLE rentals (
  RNT_ID       NUMERIC(10)   NOT NULL,
  RNT_CTR      NUMERIC(10)   NOT NULL,
  RNT_EQ       NUMERIC(10)   NOT NULL,
  RNT_ISSUE    DATE          NOT NULL,
  RNT_DUE      DATE          NOT NULL,
  RNT_RETURN   DATE,
  RNT_COND_OUT NUMERIC(2)    NOT NULL,
  RNT_COND_IN  NUMERIC(2),
  RNT_EMP      NUMERIC(6)    NOT NULL,
  RNT_COST     NUMERIC(12,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (RNT_ID),
  CONSTRAINT uniq_rnt UNIQUE (RNT_EQ, RNT_ISSUE),
  CONSTRAINT chk_rnt_due CHECK (RNT_DUE >= RNT_ISSUE),
  CONSTRAINT chk_rnt_return CHECK (RNT_RETURN IS NULL OR RNT_RETURN >= RNT_ISSUE),
  CONSTRAINT chk_rnt_cost CHECK (RNT_COST >= 0),
  CONSTRAINT fk_rnt_ctr FOREIGN KEY (RNT_CTR) REFERENCES contracts(CTR_ID),
  CONSTRAINT fk_rnt_eq  FOREIGN KEY (RNT_EQ)  REFERENCES equipment_units(EQ_ID),
  CONSTRAINT fk_rnt_cond_out FOREIGN KEY (RNT_COND_OUT) REFERENCES condition_grades(CG_ID),
  CONSTRAINT fk_rnt_cond_in  FOREIGN KEY (RNT_COND_IN)  REFERENCES condition_grades(CG_ID),
  CONSTRAINT fk_rnt_emp FOREIGN KEY (RNT_EMP) REFERENCES employees(EMP_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 21. ПЛАТЕЖИ (Payments)
-- ---------------------------------------------------------------------
CREATE TABLE payments (
  PAY_ID      NUMERIC(10)   NOT NULL,
  PAY_CTR     NUMERIC(10)   NOT NULL,
  PAY_DATE    DATE          NOT NULL,
  PAY_AMOUNT  NUMERIC(12,2) NOT NULL,
  PAY_METHOD  NUMERIC(2)    NOT NULL,
  PAY_PURPOSE VARCHAR(100),
  PAY_DOC     VARCHAR(30),
  PRIMARY KEY (PAY_ID),
  CONSTRAINT chk_pay_amount CHECK (PAY_AMOUNT > 0),
  CONSTRAINT fk_pay_ctr FOREIGN KEY (PAY_CTR) REFERENCES contracts(CTR_ID),
  CONSTRAINT fk_pay_method FOREIGN KEY (PAY_METHOD) REFERENCES payment_methods(PM_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 22. ОБСЛУЖИВАНИЕ И РЕМОНТ (Maintenance)
-- ---------------------------------------------------------------------
CREATE TABLE maintenance (
  MNT_ID         NUMERIC(10)   NOT NULL,
  MNT_EQ         NUMERIC(10)   NOT NULL,
  MNT_TYPE       NUMERIC(2)    NOT NULL,
  MNT_BEGIN      DATE          NOT NULL,
  MNT_END        DATE,
  MNT_COST       NUMERIC(10,2) NOT NULL DEFAULT 0,
  MNT_CONTRACTOR VARCHAR(100),
  MNT_RESULT     VARCHAR(200),
  PRIMARY KEY (MNT_ID),
  CONSTRAINT chk_mnt_period CHECK (MNT_END IS NULL OR MNT_END >= MNT_BEGIN),
  CONSTRAINT chk_mnt_cost CHECK (MNT_COST >= 0),
  CONSTRAINT fk_mnt_eq   FOREIGN KEY (MNT_EQ)   REFERENCES equipment_units(EQ_ID),
  CONSTRAINT fk_mnt_type FOREIGN KEY (MNT_TYPE) REFERENCES maintenance_types(MT_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
--  Готово: база данных campusrent и 22 таблицы созданы.
-- =====================================================================
