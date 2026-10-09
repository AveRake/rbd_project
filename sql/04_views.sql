-- =====================================================================
--  CampusRent — файл 04: представления (готовые запросы)
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- 1. Свободная техника по филиалам
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_available_equipment AS
SELECT b.BR_ID,
       b.BR_NAME,
       eq.EQ_ID,
       eq.EQ_INV,
       m.MOD_ID,
       CONCAT(m.MOD_BRAND, ' ', m.MOD_NAME) AS MODEL,
       c.CAT_NAME,
       cg.CG_NAME AS CONDITION_GRADE,
       eq.EQ_LOCATION
FROM equipment_units eq
JOIN branches b          ON b.BR_ID  = eq.EQ_BR
JOIN models m            ON m.MOD_ID = eq.EQ_MOD
JOIN categories c        ON c.CAT_ID = m.MOD_CAT
JOIN condition_grades cg ON cg.CG_ID = eq.EQ_COND
WHERE eq.EQ_STATUS = 'свободна';

-- ---------------------------------------------------------------------
-- 2. Текущие (невозвращённые) выдачи
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_current_rentals AS
SELECT r.RNT_ID,
       ctr.CTR_NUMBER,
       un.UN_SHORT AS UNIVERSITY,
       CONCAT(m.MOD_BRAND, ' ', m.MOD_NAME) AS MODEL,
       eq.EQ_INV,
       b.BR_ID,
       r.RNT_ISSUE,
       r.RNT_DUE,
       DATEDIFF(r.RNT_DUE, CURDATE()) AS DAYS_LEFT
FROM rentals r
JOIN contracts ctr      ON ctr.CTR_ID = r.RNT_CTR
JOIN requests rq        ON rq.REQ_ID  = ctr.CTR_REQ
JOIN universities un    ON un.UN_ID   = rq.REQ_UN
JOIN equipment_units eq ON eq.EQ_ID   = r.RNT_EQ
JOIN models m           ON m.MOD_ID   = eq.EQ_MOD
JOIN branches b         ON b.BR_ID    = eq.EQ_BR
WHERE r.RNT_RETURN IS NULL;

-- ---------------------------------------------------------------------
-- 3. Просроченные возвраты
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_overdue_rentals AS
SELECT * FROM v_current_rentals
WHERE RNT_DUE < CURDATE();

-- ---------------------------------------------------------------------
-- 4. Загрузка парка по филиалам
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_branch_load AS
SELECT b.BR_ID,
       b.BR_NAME,
       COUNT(eq.EQ_ID) AS TOTAL_UNITS,
       SUM(eq.EQ_STATUS = 'свободна')     AS FREE_UNITS,
       SUM(eq.EQ_STATUS = 'аренда')       AS RENTED_UNITS,
       SUM(eq.EQ_STATUS = 'обслуживание') AS MAINTENANCE_UNITS,
       SUM(eq.EQ_STATUS = 'списана')      AS WRITTEN_OFF,
       ROUND(100 * SUM(eq.EQ_STATUS = 'аренда') / COUNT(eq.EQ_ID), 1) AS LOAD_PERCENT
FROM branches b
LEFT JOIN equipment_units eq ON eq.EQ_BR = b.BR_ID
GROUP BY b.BR_ID, b.BR_NAME;

-- ---------------------------------------------------------------------
-- 5. Сводный парк по филиалам (консолидированная копия)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_consolidated_fleet AS
SELECT c.CAT_NAME,
       CONCAT(m.MOD_BRAND, ' ', m.MOD_NAME) AS MODEL,
       b.BR_ID,
       COUNT(eq.EQ_ID) AS UNITS,
       SUM(eq.EQ_STATUS = 'аренда') AS RENTED,
       SUM(eq.EQ_STATUS = 'свободна') AS FREE
FROM equipment_units eq
JOIN models m     ON m.MOD_ID = eq.EQ_MOD
JOIN categories c ON c.CAT_ID = m.MOD_CAT
JOIN branches b   ON b.BR_ID  = eq.EQ_BR
GROUP BY c.CAT_NAME, MODEL, b.BR_ID;

-- ---------------------------------------------------------------------
-- 6. Заявки своего филиала (обновляемое представление для сотрудников филиала)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_my_branch_requests AS
SELECT *
FROM requests
WHERE REQ_BR = (SELECT e.EMP_BR FROM employees e
                WHERE e.EMP_LOGIN = SUBSTRING_INDEX(USER(), '@', 1))
WITH CHECK OPTION;

-- ---------------------------------------------------------------------
-- 7. Заявки своего вуза (обновляемое представление для представителя вуза)
--    Учётная запись представителя имеет вид univ_<UN_ID>
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_my_university_requests AS
SELECT *
FROM requests
WHERE REQ_UN = CAST(REPLACE(SUBSTRING_INDEX(USER(), '@', 1), 'univ_', '') AS UNSIGNED)
WITH CHECK OPTION;

-- ---------------------------------------------------------------------
-- 8. Договоры своего вуза (представление для чтения)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_my_university_contracts AS
SELECT ctr.CTR_ID,
       ctr.CTR_NUMBER,
       un.UN_SHORT AS UNIVERSITY,
       ctr.CTR_SIGN,
       ctr.CTR_BEGIN,
       ctr.CTR_END,
       ctr.CTR_SUM,
       ctr.CTR_STATUS
FROM contracts ctr
JOIN requests rq     ON rq.REQ_ID = ctr.CTR_REQ
JOIN universities un ON un.UN_ID  = rq.REQ_UN
WHERE rq.REQ_UN = CAST(REPLACE(SUBSTRING_INDEX(USER(), '@', 1), 'univ_', '') AS UNSIGNED);

-- ---------------------------------------------------------------------
-- 9. Заявки с полной детализацией (для отчётности)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_request_full AS
SELECT rq.REQ_ID,
       rq.REQ_NUMBER,
       un.UN_SHORT AS UNIVERSITY,
       un.UN_CITY,
       rq.REQ_BR,
       d.DEP_NAME,
       rs.RST_NAME AS STATUS,
       rq.REQ_CREATED,
       rq.REQ_BEGIN,
       rq.REQ_END,
       rq.REQ_SUM,
       CONCAT(m.MOD_BRAND, ' ', m.MOD_NAME) AS MODEL,
       ri.RIT_QTY,
       ri.RIT_COST
FROM requests rq
JOIN universities un     ON un.UN_ID  = rq.REQ_UN
JOIN departments d       ON d.DEP_ID  = rq.REQ_DEP
JOIN request_statuses rs ON rs.RST_ID = rq.REQ_STATUS
JOIN request_items ri    ON ri.RIT_REQ = rq.REQ_ID
JOIN models m            ON m.MOD_ID  = ri.RIT_MOD;

-- ---------------------------------------------------------------------
-- 10. ВУЗы-должники (невозвращённая техника с истёкшим сроком)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_debtors AS
SELECT un.UN_ID,
       un.UN_SHORT AS UNIVERSITY,
       COUNT(*) AS OVERDUE_ITEMS,
       MIN(r.RNT_DUE) AS OLDEST_DUE
FROM rentals r
JOIN contracts ctr   ON ctr.CTR_ID = r.RNT_CTR
JOIN requests rq     ON rq.REQ_ID  = ctr.CTR_REQ
JOIN universities un ON un.UN_ID   = rq.REQ_UN
WHERE r.RNT_RETURN IS NULL AND r.RNT_DUE < CURDATE()
GROUP BY un.UN_ID, un.UN_SHORT;
