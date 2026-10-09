-- =====================================================================
--  CampusRent — проверка ограничений целостности (триггеры и CHECK).
--  Файл рассчитан на запуск с ключом --force: часть инструкций ДОЛЖНА
--  завершиться ошибкой — это и есть ожидаемый результат теста.
--  В комментариях указан ожидаемый результат.
-- =====================================================================

USE campusrent;
SET NAMES utf8mb4;

SELECT '=========== ТЕСТЫ ОГРАНИЧЕНИЙ ЦЕЛОСТНОСТИ ===========' AS `Проверка`;

-- ---------------------------------------------------------------------
-- P1. Корректная заявка (должна пройти успешно)
-- ---------------------------------------------------------------------
SELECT '--- P1: корректная заявка (ожидается успех) ---' AS `Тест`;
DELETE FROM request_items WHERE RIT_REQ = 999000;
DELETE FROM requests WHERE REQ_ID = 999000;
INSERT INTO requests (REQ_ID, REQ_NUMBER, REQ_UN, REQ_DEP, REQ_REP, REQ_BR,
                      REQ_CREATED, REQ_BEGIN, REQ_END, REQ_STATUS, REQ_SUM)
VALUES (999000, 'TST-0001', 1001, 2001, 3001, 'HQ',
        '2026-10-01', '2026-10-15', '2026-10-20', 2, 0);
SELECT 'P1: заявка добавлена успешно' AS `Результат`;

-- ---------------------------------------------------------------------
-- N1. Заявка с чужим филиалом (ожидается ОШИБКА триггера)
-- ---------------------------------------------------------------------
SELECT '--- N1: заявка с филиалом другого региона (ожидается ошибка) ---' AS `Тест`;
INSERT INTO requests (REQ_ID, REQ_NUMBER, REQ_UN, REQ_DEP, REQ_REP, REQ_BR,
                      REQ_CREATED, REQ_BEGIN, REQ_END, REQ_STATUS, REQ_SUM)
VALUES (999001, 'TST-0002', 1001, 2001, 3001, 'SPB',
        '2026-10-01', '2026-10-15', '2026-10-20', 2, 0);

-- ---------------------------------------------------------------------
-- N2. Позиция с тарифом другой модели (ожидается ОШИБКА триггера)
-- ---------------------------------------------------------------------
SELECT '--- N2: тариф не соответствует модели (ожидается ошибка) ---' AS `Тест`;
INSERT INTO request_items (RIT_ID, RIT_REQ, RIT_MOD, RIT_QTY, RIT_BEGIN, RIT_END, RIT_TAR, RIT_COST)
VALUES (999001, 999000, 201, 1, '2026-10-15', '2026-10-20', 1011, 100);

-- ---------------------------------------------------------------------
-- P2. Корректная позиция (должна пройти; REQ_SUM пересчитывается триггером)
-- ---------------------------------------------------------------------
SELECT '--- P2: корректная позиция (ожидается успех) ---' AS `Тест`;
INSERT INTO request_items (RIT_ID, RIT_REQ, RIT_MOD, RIT_QTY, RIT_BEGIN, RIT_END, RIT_TAR, RIT_COST)
VALUES (999002, 999000, 201, 2, '2026-10-15', '2026-10-20', 2011, 7440.00);
SELECT REQ_ID, REQ_SUM AS `Сумма пересчитана триггером` FROM requests WHERE REQ_ID = 999000;

-- ---------------------------------------------------------------------
-- N3. Позиция с периодом за пределами заявки (ожидается ОШИБКА)
-- ---------------------------------------------------------------------
SELECT '--- N3: период позиции вне периода заявки (ожидается ошибка) ---' AS `Тест`;
INSERT INTO request_items (RIT_ID, RIT_REQ, RIT_MOD, RIT_QTY, RIT_BEGIN, RIT_END, RIT_TAR, RIT_COST)
VALUES (999003, 999000, 202, 1, '2026-11-01', '2026-11-10', 2021, 500);

-- ---------------------------------------------------------------------
-- N4. Сумма заявки изменена вручную неверно (ожидается ОШИБКА)
-- ---------------------------------------------------------------------
SELECT '--- N4: неверная сумма заявки (ожидается ошибка) ---' AS `Тест`;
UPDATE requests SET REQ_SUM = 999999 WHERE REQ_ID = 999000;

-- ---------------------------------------------------------------------
-- N5. Недопустимый статус экземпляра техники (ожидается ошибка CHECK)
-- ---------------------------------------------------------------------
SELECT '--- N5: недопустимый статус техники (ожидается ошибка CHECK) ---' AS `Тест`;
INSERT INTO equipment_units (EQ_ID, EQ_INV, EQ_MOD, EQ_BR, EQ_STATUS, EQ_COND,
                             EQ_ACQUIRE, EQ_LOCATION)
VALUES (999999, 'TST-99999999', 101, 'HQ', 'в ремонте', 3, '2026-01-01', 'Тестовый склад');

-- ---------------------------------------------------------------------
-- N6. Дублирование паспорта представителя (ожидается ошибка UNIQUE)
-- ---------------------------------------------------------------------
SELECT '--- N6: дубликат паспорта (ожидается ошибка) ---' AS `Тест`;
INSERT INTO representatives (REP_ID, REP_UN, REP_DEP, REP_FIO, REP_POSITION,
                             REP_PHONE, REP_EMAIL, REP_PASSPORT)
SELECT 999002, 1001, 2001, 'Тестов Тест Тестович', 'специалист',
       '+7 900 000-00-00', 'test@edu.ru', REP_PASSPORT
FROM representatives WHERE REP_ID = 3001;

-- ---------------------------------------------------------------------
-- N7. Пересекающиеся периоды выдачи одного экземпляра (ожидается ОШИБКА)
-- ---------------------------------------------------------------------
SELECT '--- N7: пересечение выдач одного экземпляра (ожидается ошибка) ---' AS `Тест`;
SET @eq  := (SELECT RNT_EQ    FROM rentals WHERE RNT_RETURN IS NOT NULL ORDER BY RNT_ID LIMIT 1);
SET @ctr := (SELECT RNT_CTR   FROM rentals WHERE RNT_EQ = @eq LIMIT 1);
SET @b   := (SELECT RNT_ISSUE FROM rentals WHERE RNT_EQ = @eq LIMIT 1);
SET @e   := (SELECT RNT_DUE   FROM rentals WHERE RNT_EQ = @eq LIMIT 1);
INSERT INTO rentals (RNT_ID, RNT_CTR, RNT_EQ, RNT_ISSUE, RNT_DUE, RNT_RETURN,
                     RNT_COND_OUT, RNT_COND_IN, RNT_EMP, RNT_COST)
VALUES (999001, @ctr, @eq, @b, @e, NULL, 3, NULL, 6, 100.00);

-- ---------------------------------------------------------------------
-- N8. Выдача экземпляра, который уже находится в аренде (ожидается ОШИБКА)
-- ---------------------------------------------------------------------
SELECT '--- N8: выдача занятого экземпляра (ожидается ошибка) ---' AS `Тест`;
SET @eq2  := (SELECT EQ_ID FROM equipment_units WHERE EQ_STATUS = 'аренда' LIMIT 1);
SET @ctr2 := (SELECT r.RNT_CTR FROM rentals r JOIN request_items ri ON ri.RIT_REQ =
               (SELECT CTR_REQ FROM contracts WHERE CTR_ID = r.RNT_CTR)
              WHERE r.RNT_EQ = @eq2 LIMIT 1);
INSERT INTO rentals (RNT_ID, RNT_CTR, RNT_EQ, RNT_ISSUE, RNT_DUE, RNT_RETURN,
                     RNT_COND_OUT, RNT_COND_IN, RNT_EMP, RNT_COST)
VALUES (999002, @ctr2, @eq2, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 5 DAY), NULL, 3, NULL, 6, 100.00);

-- ---------------------------------------------------------------------
-- P3. Возврат техники (ожидается успех; статус экземпляра меняется)
-- ---------------------------------------------------------------------
SELECT '--- P3: возврат техники (ожидается успех) ---' AS `Тест`;
SET @rnt := (SELECT RNT_ID FROM rentals WHERE RNT_RETURN IS NULL ORDER BY RNT_ID LIMIT 1);
SET @eq3 := (SELECT RNT_EQ FROM rentals WHERE RNT_ID = @rnt);
SELECT EQ_ID, EQ_STATUS AS `Статус до возврата` FROM equipment_units WHERE EQ_ID = @eq3;
UPDATE rentals SET RNT_RETURN = RNT_DUE, RNT_COND_IN = 3 WHERE RNT_ID = @rnt;
SELECT EQ_ID, EQ_STATUS AS `Статус после возврата` FROM equipment_units WHERE EQ_ID = @eq3;

-- Очистка тестовых записей
DELETE FROM request_items WHERE RIT_REQ = 999000;
DELETE FROM requests WHERE REQ_ID = 999000;

SELECT '=========== ТЕСТЫ ЗАВЕРШЕНЫ ===========' AS `Проверка`;
