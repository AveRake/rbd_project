-- =====================================================================
--  CampusRent — файл 05: триггеры (реализация ограничений целостности)
--  ВНИМАНИЕ: файл выполняется ПОСЛЕ загрузки тестовых данных
--  (03_test_data.sql), иначе триггеры будут проверять каждую строку
--  при массовой загрузке.
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

DELIMITER $$

-- ---------------------------------------------------------------------
-- 1. Согласованность заявки: филиал, подразделение, представитель
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_requests_bi$$
CREATE TRIGGER trg_requests_bi BEFORE INSERT ON requests
FOR EACH ROW
BEGIN
  DECLARE v_br     VARCHAR(8);
  DECLARE v_dep_un NUMERIC(6);
  DECLARE v_rep_un NUMERIC(6);

  SELECT UN_BR INTO v_br FROM universities WHERE UN_ID = NEW.REQ_UN;
  IF v_br IS NOT NULL AND NEW.REQ_BR <> v_br THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: филиал не совпадает с обслуживающим филиалом вуза';
  END IF;

  SELECT DEP_UN INTO v_dep_un FROM departments WHERE DEP_ID = NEW.REQ_DEP;
  IF v_dep_un IS NOT NULL AND v_dep_un <> NEW.REQ_UN THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: подразделение принадлежит другому вузу';
  END IF;

  SELECT REP_UN INTO v_rep_un FROM representatives WHERE REP_ID = NEW.REQ_REP;
  IF v_rep_un IS NOT NULL AND v_rep_un <> NEW.REQ_UN THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: представитель принадлежит другому вузу';
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_requests_bu$$
CREATE TRIGGER trg_requests_bu BEFORE UPDATE ON requests
FOR EACH ROW
BEGIN
  DECLARE v_br     VARCHAR(8);
  DECLARE v_dep_un NUMERIC(6);
  DECLARE v_rep_un NUMERIC(6);

  SELECT UN_BR INTO v_br FROM universities WHERE UN_ID = NEW.REQ_UN;
  IF v_br IS NOT NULL AND NEW.REQ_BR <> v_br THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: филиал не совпадает с обслуживающим филиалом вуза';
  END IF;

  SELECT DEP_UN INTO v_dep_un FROM departments WHERE DEP_ID = NEW.REQ_DEP;
  IF v_dep_un IS NOT NULL AND v_dep_un <> NEW.REQ_UN THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: подразделение принадлежит другому вузу';
  END IF;

  SELECT REP_UN INTO v_rep_un FROM representatives WHERE REP_ID = NEW.REQ_REP;
  IF v_rep_un IS NOT NULL AND v_rep_un <> NEW.REQ_UN THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: представитель принадлежит другому вузу';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 2. Позиция заявки: тариф соответствует модели, периоды согласованы
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_rit_bi$$
CREATE TRIGGER trg_rit_bi BEFORE INSERT ON request_items
FOR EACH ROW
BEGIN
  DECLARE v_tar_mod NUMERIC(6);
  DECLARE v_tar_b   DATE;
  DECLARE v_tar_e   DATE;
  DECLARE v_req_b   DATE;
  DECLARE v_req_e   DATE;

  SELECT TAR_MOD, TAR_BEGIN, TAR_END INTO v_tar_mod, v_tar_b, v_tar_e
    FROM tariffs WHERE TAR_ID = NEW.RIT_TAR;
  IF v_tar_mod IS NOT NULL AND v_tar_mod <> NEW.RIT_MOD THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Позиция заявки: тариф относится к другой модели';
  END IF;
  IF v_tar_b IS NOT NULL AND
     (NEW.RIT_BEGIN < v_tar_b OR (v_tar_e IS NOT NULL AND NEW.RIT_END > v_tar_e)) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Позиция заявки: период выходит за период действия тарифа';
  END IF;

  SELECT REQ_BEGIN, REQ_END INTO v_req_b, v_req_e
    FROM requests WHERE REQ_ID = NEW.RIT_REQ;
  IF v_req_b IS NOT NULL AND (NEW.RIT_BEGIN < v_req_b OR NEW.RIT_END > v_req_e) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Позиция заявки: период выходит за период заявки';
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_rit_bu$$
CREATE TRIGGER trg_rit_bu BEFORE UPDATE ON request_items
FOR EACH ROW
BEGIN
  DECLARE v_tar_mod NUMERIC(6);
  DECLARE v_tar_b   DATE;
  DECLARE v_tar_e   DATE;
  DECLARE v_req_b   DATE;
  DECLARE v_req_e   DATE;

  SELECT TAR_MOD, TAR_BEGIN, TAR_END INTO v_tar_mod, v_tar_b, v_tar_e
    FROM tariffs WHERE TAR_ID = NEW.RIT_TAR;
  IF v_tar_mod IS NOT NULL AND v_tar_mod <> NEW.RIT_MOD THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Позиция заявки: тариф относится к другой модели';
  END IF;
  IF v_tar_b IS NOT NULL AND
     (NEW.RIT_BEGIN < v_tar_b OR (v_tar_e IS NOT NULL AND NEW.RIT_END > v_tar_e)) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Позиция заявки: период выходит за период действия тарифа';
  END IF;

  SELECT REQ_BEGIN, REQ_END INTO v_req_b, v_req_e
    FROM requests WHERE REQ_ID = NEW.RIT_REQ;
  IF v_req_b IS NOT NULL AND (NEW.RIT_BEGIN < v_req_b OR NEW.RIT_END > v_req_e) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Позиция заявки: период выходит за период заявки';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 3. Поддержание суммы заявки (REQ_SUM = сумма позиций)
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_rit_ai$$
CREATE TRIGGER trg_rit_ai AFTER INSERT ON request_items
FOR EACH ROW
BEGIN
  UPDATE requests r
     SET r.REQ_SUM = (SELECT COALESCE(SUM(ri.RIT_COST), 0)
                        FROM request_items ri WHERE ri.RIT_REQ = NEW.RIT_REQ)
   WHERE r.REQ_ID = NEW.RIT_REQ;
END$$

DROP TRIGGER IF EXISTS trg_rit_au$$
CREATE TRIGGER trg_rit_au AFTER UPDATE ON request_items
FOR EACH ROW
BEGIN
  UPDATE requests r
     SET r.REQ_SUM = (SELECT COALESCE(SUM(ri.RIT_COST), 0)
                        FROM request_items ri WHERE ri.RIT_REQ = NEW.RIT_REQ)
   WHERE r.REQ_ID = NEW.RIT_REQ;
END$$

DROP TRIGGER IF EXISTS trg_rit_ad$$
CREATE TRIGGER trg_rit_ad AFTER DELETE ON request_items
FOR EACH ROW
BEGIN
  UPDATE requests r
     SET r.REQ_SUM = (SELECT COALESCE(SUM(ri.RIT_COST), 0)
                        FROM request_items ri WHERE ri.RIT_REQ = OLD.RIT_REQ)
   WHERE r.REQ_ID = OLD.RIT_REQ;
END$$

-- Проверка, что сумму заявки нельзя изменить «вручную» неверно
DROP TRIGGER IF EXISTS trg_req_bu_sum$$
CREATE TRIGGER trg_req_bu_sum BEFORE UPDATE ON requests
FOR EACH ROW
BEGIN
  DECLARE v_sum NUMERIC(12,2);
  SELECT COALESCE(SUM(ri.RIT_COST), 0) INTO v_sum
    FROM request_items ri WHERE ri.RIT_REQ = NEW.REQ_ID;
  IF NEW.REQ_SUM <> v_sum THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Заявка: сумма не равна сумме позиций';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 4. Выдачи: доступность экземпляра, соответствие модели, пересечение
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_rentals_bi$$
CREATE TRIGGER trg_rentals_bi BEFORE INSERT ON rentals
FOR EACH ROW
BEGIN
  DECLARE v_status VARCHAR(12);
  DECLARE v_mod    NUMERIC(6);
  DECLARE v_cnt    INT;
  DECLARE v_ctr_b  DATE;
  DECLARE v_ctr_e  DATE;

  SELECT EQ_STATUS, EQ_MOD INTO v_status, v_mod
    FROM equipment_units WHERE EQ_ID = NEW.RNT_EQ;
  IF v_status IS NOT NULL AND v_status NOT IN ('свободна','бронь') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Выдача: экземпляр не свободен';
  END IF;

  SELECT COUNT(*) INTO v_cnt
    FROM request_items ri
    JOIN contracts c ON c.CTR_REQ = ri.RIT_REQ
   WHERE c.CTR_ID = NEW.RNT_CTR AND ri.RIT_MOD = v_mod;
  IF v_cnt = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Выдача: модель экземпляра не соответствует позиции заявки';
  END IF;

  SELECT CTR_BEGIN, CTR_END INTO v_ctr_b, v_ctr_e
    FROM contracts WHERE CTR_ID = NEW.RNT_CTR;
  IF v_ctr_b IS NOT NULL AND (NEW.RNT_ISSUE < v_ctr_b OR NEW.RNT_DUE > v_ctr_e) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Выдача: период выходит за период договора';
  END IF;

  SELECT COUNT(*) INTO v_cnt FROM rentals r
   WHERE r.RNT_EQ = NEW.RNT_EQ
     AND r.RNT_ID <> NEW.RNT_ID
     AND NEW.RNT_ISSUE <= COALESCE(r.RNT_RETURN, r.RNT_DUE)
     AND r.RNT_ISSUE <= COALESCE(NEW.RNT_RETURN, NEW.RNT_DUE);
  IF v_cnt > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Выдача: периоды выдач одного экземпляра пересекаются';
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_rentals_bu$$
CREATE TRIGGER trg_rentals_bu BEFORE UPDATE ON rentals
FOR EACH ROW
BEGIN
  DECLARE v_cnt INT;
  SELECT COUNT(*) INTO v_cnt FROM rentals r
   WHERE r.RNT_EQ = NEW.RNT_EQ
     AND r.RNT_ID <> NEW.RNT_ID
     AND NEW.RNT_ISSUE <= COALESCE(r.RNT_RETURN, r.RNT_DUE)
     AND r.RNT_ISSUE <= COALESCE(NEW.RNT_RETURN, NEW.RNT_DUE);
  IF v_cnt > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Выдача: периоды выдач одного экземпляра пересекаются';
  END IF;
END$$

-- При выдаче экземпляр переводится в статус «аренда»
DROP TRIGGER IF EXISTS trg_rentals_ai$$
CREATE TRIGGER trg_rentals_ai AFTER INSERT ON rentals
FOR EACH ROW
BEGIN
  IF NEW.RNT_RETURN IS NULL THEN
    UPDATE equipment_units SET EQ_STATUS = 'аренда' WHERE EQ_ID = NEW.RNT_EQ;
  ELSE
    UPDATE equipment_units SET EQ_STATUS = 'свободна' WHERE EQ_ID = NEW.RNT_EQ;
  END IF;
END$$

-- При возврате экземпляр снова свободен, фиксируется состояние
DROP TRIGGER IF EXISTS trg_rentals_au$$
CREATE TRIGGER trg_rentals_au AFTER UPDATE ON rentals
FOR EACH ROW
BEGIN
  IF NEW.RNT_RETURN IS NOT NULL AND OLD.RNT_RETURN IS NULL THEN
    UPDATE equipment_units
       SET EQ_STATUS = 'свободна'
     WHERE EQ_ID = NEW.RNT_EQ;
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 5. Поддержание суммы договора (CTR_SUM = сумма выдач)
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_rnt_ai$$
CREATE TRIGGER trg_rnt_ai AFTER INSERT ON rentals
FOR EACH ROW
BEGIN
  UPDATE contracts c
     SET c.CTR_SUM = (SELECT COALESCE(SUM(r.RNT_COST), 0)
                        FROM rentals r WHERE r.RNT_CTR = NEW.RNT_CTR)
   WHERE c.CTR_ID = NEW.RNT_CTR;
END$$

DROP TRIGGER IF EXISTS trg_rnt_au$$
CREATE TRIGGER trg_rnt_au AFTER UPDATE ON rentals
FOR EACH ROW
BEGIN
  UPDATE contracts c
     SET c.CTR_SUM = (SELECT COALESCE(SUM(r.RNT_COST), 0)
                        FROM rentals r WHERE r.RNT_CTR = NEW.RNT_CTR)
   WHERE c.CTR_ID = NEW.RNT_CTR;
END$$

DROP TRIGGER IF EXISTS trg_rnt_ad$$
CREATE TRIGGER trg_rnt_ad AFTER DELETE ON rentals
FOR EACH ROW
BEGIN
  UPDATE contracts c
     SET c.CTR_SUM = (SELECT COALESCE(SUM(r.RNT_COST), 0)
                        FROM rentals r WHERE r.RNT_CTR = OLD.RNT_CTR)
   WHERE c.CTR_ID = OLD.RNT_CTR;
END$$

DROP TRIGGER IF EXISTS trg_ctr_bu_sum$$
CREATE TRIGGER trg_ctr_bu_sum BEFORE UPDATE ON contracts
FOR EACH ROW
BEGIN
  DECLARE v_sum NUMERIC(12,2);
  SELECT COALESCE(SUM(r.RNT_COST), 0) INTO v_sum
    FROM rentals r WHERE r.RNT_CTR = NEW.CTR_ID;
  IF NEW.CTR_SUM <> v_sum THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Договор: сумма не равна сумме выдач';
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 6. Тарифы: запрет пересечения периодов действия
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_tariff_bi$$
CREATE TRIGGER trg_tariff_bi BEFORE INSERT ON tariffs
FOR EACH ROW
BEGIN
  DECLARE v_cnt INT;
  SELECT COUNT(*) INTO v_cnt FROM tariffs t
   WHERE t.TAR_MOD = NEW.TAR_MOD AND t.TAR_UNIT = NEW.TAR_UNIT
     AND NEW.TAR_BEGIN <= COALESCE(t.TAR_END, '9999-12-31')
     AND t.TAR_BEGIN <= COALESCE(NEW.TAR_END, '9999-12-31');
  IF v_cnt > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Тариф: период действия пересекается с существующим';
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_tariff_bu$$
CREATE TRIGGER trg_tariff_bu BEFORE UPDATE ON tariffs
FOR EACH ROW
BEGIN
  DECLARE v_cnt INT;
  SELECT COUNT(*) INTO v_cnt FROM tariffs t
   WHERE t.TAR_MOD = NEW.TAR_MOD AND t.TAR_UNIT = NEW.TAR_UNIT
     AND t.TAR_ID <> NEW.TAR_ID
     AND NEW.TAR_BEGIN <= COALESCE(t.TAR_END, '9999-12-31')
     AND t.TAR_BEGIN <= COALESCE(NEW.TAR_END, '9999-12-31');
  IF v_cnt > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Тариф: период действия пересекается с существующим';
  END IF;
END$$

DELIMITER ;

-- =====================================================================
--  Триггеры созданы.
-- =====================================================================
