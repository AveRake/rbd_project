-- =====================================================================
--  CampusRent — файл 08: отчётные запросы
--  Запросы используются как готовые отчётные формы и как источник
--  данных для диаграмм итогового отчёта.
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- ЗАПРОС 1. Количество свободной техники по филиалам и категориям
-- ---------------------------------------------------------------------
SELECT b.BR_ID                        AS `Филиал`,
       b.BR_CITY                      AS `Город`,
       c.CAT_NAME                     AS `Категория`,
       COUNT(*)                       AS `Свободно, шт`
FROM equipment_units eq
JOIN branches b   ON b.BR_ID  = eq.EQ_BR
JOIN models m     ON m.MOD_ID = eq.EQ_MOD
JOIN categories c ON c.CAT_ID = m.MOD_CAT
WHERE eq.EQ_STATUS = 'свободна'
GROUP BY b.BR_ID, b.BR_CITY, c.CAT_NAME
ORDER BY b.BR_ID, `Свободно, шт` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 2. Загрузка парка по филиалам
-- ---------------------------------------------------------------------
SELECT * FROM v_branch_load ORDER BY LOAD_PERCENT DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 3. Текущие (невозвращённые) выдачи
-- ---------------------------------------------------------------------
SELECT UNIVERSITY, MODEL, EQ_INV, BR_ID, RNT_ISSUE, RNT_DUE, DAYS_LEFT
FROM v_current_rentals
ORDER BY RNT_DUE
LIMIT 50;

-- ---------------------------------------------------------------------
-- ЗАПРОС 4. Просроченные возвраты
-- ---------------------------------------------------------------------
SELECT UNIVERSITY, MODEL, EQ_INV, BR_ID, RNT_DUE,
       DATEDIFF(CURDATE(), RNT_DUE) AS `Просрочка, дней`
FROM v_overdue_rentals
ORDER BY `Просрочка, дней` DESC
LIMIT 50;

-- ---------------------------------------------------------------------
-- ЗАПРОС 5. ТОП-10 моделей техники по числу выдач
-- ---------------------------------------------------------------------
SELECT CONCAT(m.MOD_BRAND, ' ', m.MOD_NAME) AS `Модель`,
       c.CAT_NAME                            AS `Категория`,
       COUNT(*)                              AS `Выдач`
FROM rentals r
JOIN equipment_units eq ON eq.EQ_ID = r.RNT_EQ
JOIN models m           ON m.MOD_ID = eq.EQ_MOD
JOIN categories c       ON c.CAT_ID = m.MOD_CAT
GROUP BY `Модель`, `Категория`
ORDER BY `Выдач` DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- ЗАПРОС 6. Выручка (поступления платежей) по филиалам
-- ---------------------------------------------------------------------
SELECT b.BR_ID                AS `Филиал`,
       b.BR_NAME              AS `Название`,
       COUNT(DISTINCT ctr.CTR_ID) AS `Договоров`,
       ROUND(SUM(p.PAY_AMOUNT), 2) AS `Поступления, руб`
FROM payments p
JOIN contracts ctr ON ctr.CTR_ID = p.PAY_CTR
JOIN requests rq   ON rq.REQ_ID  = ctr.CTR_REQ
JOIN branches b    ON b.BR_ID    = rq.REQ_BR
GROUP BY b.BR_ID, b.BR_NAME
ORDER BY `Поступления, руб` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 7. Динамика поступлений по месяцам
-- ---------------------------------------------------------------------
SELECT DATE_FORMAT(p.PAY_DATE, '%Y-%m') AS `Месяц`,
       COUNT(*)                         AS `Платежей`,
       ROUND(SUM(p.PAY_AMOUNT), 2)      AS `Сумма, руб`
FROM payments p
GROUP BY `Месяц`
ORDER BY `Месяц`;

-- ---------------------------------------------------------------------
-- ЗАПРОС 8. Структура парка техники по категориям
-- ---------------------------------------------------------------------
SELECT c.CAT_NAME AS `Категория`,
       COUNT(*)   AS `Экземпляров`,
       SUM(eq.EQ_STATUS = 'свободна') AS `Свободно`,
       SUM(eq.EQ_STATUS = 'аренда')   AS `В аренде`,
       ROUND(100 * SUM(eq.EQ_STATUS = 'аренда') / COUNT(*), 1) AS `Загрузка, %`
FROM equipment_units eq
JOIN models m     ON m.MOD_ID = eq.EQ_MOD
JOIN categories c ON c.CAT_ID = m.MOD_CAT
GROUP BY c.CAT_NAME
ORDER BY `Экземпляров` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 9. Заявки по статусам
-- ---------------------------------------------------------------------
SELECT rs.RST_NAME AS `Статус`,
       COUNT(*)    AS `Заявок`,
       ROUND(SUM(rq.REQ_SUM), 2) AS `Сумма, руб`
FROM requests rq
JOIN request_statuses rs ON rs.RST_ID = rq.REQ_STATUS
GROUP BY rs.RST_NAME
ORDER BY `Заявок` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 10. ТОП-10 вузов по сумме заявок
-- ---------------------------------------------------------------------
SELECT un.UN_SHORT AS `ВУЗ`,
       un.UN_CITY  AS `Город`,
       COUNT(*)    AS `Заявок`,
       ROUND(SUM(rq.REQ_SUM), 2) AS `Сумма, руб`
FROM requests rq
JOIN universities un ON un.UN_ID = rq.REQ_UN
GROUP BY un.UN_SHORT, un.UN_CITY
ORDER BY `Сумма, руб` DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- ЗАПРОС 11. Затраты на обслуживание и ремонт по видам работ
-- ---------------------------------------------------------------------
SELECT mt.MT_NAME AS `Вид работ`,
       COUNT(*)   AS `Работ`,
       ROUND(SUM(mn.MNT_COST), 2) AS `Затраты, руб`,
       ROUND(AVG(mn.MNT_COST), 2) AS `Средняя стоимость, руб`
FROM maintenance mn
JOIN maintenance_types mt ON mt.MT_ID = mn.MNT_TYPE
GROUP BY mt.MT_NAME
ORDER BY `Затраты, руб` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 12. Средняя длительность аренды по категориям
-- ---------------------------------------------------------------------
SELECT c.CAT_NAME AS `Категория`,
       COUNT(*)   AS `Выдач`,
       ROUND(AVG(DATEDIFF(COALESCE(r.RNT_RETURN, r.RNT_DUE), r.RNT_ISSUE)), 1) AS `Средний срок, дней`
FROM rentals r
JOIN equipment_units eq ON eq.EQ_ID = r.RNT_EQ
JOIN models m           ON m.MOD_ID = eq.EQ_MOD
JOIN categories c       ON c.CAT_ID = m.MOD_CAT
GROUP BY c.CAT_NAME
ORDER BY `Средний срок, дней` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 13. ВУЗы с просроченной задолженностью
-- ---------------------------------------------------------------------
SELECT UNIVERSITY AS `ВУЗ`, OVERDUE_ITEMS AS `Просрочено, шт`, OLDEST_DUE AS `Старейший срок`
FROM v_debtors
ORDER BY OVERDUE_ITEMS DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- ЗАПРОС 14. Состояние парка техники
-- ---------------------------------------------------------------------
SELECT cg.CG_NAME AS `Состояние`,
       COUNT(*)   AS `Экземпляров`
FROM equipment_units eq
JOIN condition_grades cg ON cg.CG_ID = eq.EQ_COND
GROUP BY cg.CG_NAME
ORDER BY `Экземпляров` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 15. РАСПРЕДЕЛЁННЫЙ ЗАПРОС:
-- в каких филиалах есть свободная техника заданной модели?
-- (параметр MOD_ID = 201 — проектор Epson EB-X51)
-- ---------------------------------------------------------------------
SELECT eq.EQ_BR AS `Филиал`,
       b.BR_CITY AS `Город`,
       COUNT(*)  AS `Свободно, шт`
FROM equipment_units eq
JOIN branches b ON b.BR_ID = eq.EQ_BR
WHERE eq.EQ_MOD = 201 AND eq.EQ_STATUS = 'свободна'
GROUP BY eq.EQ_BR, b.BR_CITY
ORDER BY `Свободно, шт` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 16. Эффективность филиалов
-- ---------------------------------------------------------------------
SELECT b.BR_ID                       AS `Филиал`,
       COUNT(DISTINCT ctr.CTR_ID)    AS `Договоров`,
       COUNT(DISTINCT r.RNT_EQ)      AS `Задействовано единиц`,
       ROUND(AVG(r.RNT_COST), 2)     AS `Средний чек, руб`
FROM contracts ctr
JOIN requests rq   ON rq.REQ_ID  = ctr.CTR_REQ
JOIN branches b    ON b.BR_ID    = rq.REQ_BR
LEFT JOIN rentals r ON r.RNT_CTR = ctr.CTR_ID
GROUP BY b.BR_ID
ORDER BY `Договоров` DESC;

-- ---------------------------------------------------------------------
-- ЗАПРОС 17. Перемещения техники между филиалами
-- ---------------------------------------------------------------------
SELECT t.TR_DATE AS `Дата`,
       t.TR_FROM AS `Откуда`,
       t.TR_TO   AS `Куда`,
       eq.EQ_INV AS `Инвентарный номер`,
       CONCAT(m.MOD_BRAND, ' ', m.MOD_NAME) AS `Модель`,
       t.TR_REASON AS `Причина`
FROM transfers t
JOIN equipment_units eq ON eq.EQ_ID = t.TR_EQ
JOIN models m           ON m.MOD_ID = eq.EQ_MOD
ORDER BY t.TR_DATE DESC
LIMIT 40;

-- ---------------------------------------------------------------------
-- ЗАПРОС 18. Распределение парка по филиалам и категориям (консолидация)
-- ---------------------------------------------------------------------
SELECT BR_ID AS `Филиал`, CAT_NAME AS `Категория`,
       SUM(UNITS) AS `Экземпляров`, SUM(RENTED) AS `В аренде`, SUM(FREE) AS `Свободно`
FROM v_consolidated_fleet
GROUP BY BR_ID, CAT_NAME
ORDER BY BR_ID, `Экземпляров` DESC;
