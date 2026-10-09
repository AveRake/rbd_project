<?php
// CampusRent — отчётные формы (результаты запросов из sql/08_queries.sql).
require __DIR__ . '/config.php';

$reports = [
    'Загрузка парка по филиалам' => 'SELECT * FROM v_branch_load ORDER BY LOAD_PERCENT DESC',
    'ТОП-10 моделей по числу выдач' =>
        "SELECT CONCAT(m.MOD_BRAND,' ',m.MOD_NAME) AS model, c.CAT_NAME AS category,
                COUNT(*) AS cnt
           FROM rentals r
           JOIN equipment_units eq ON eq.EQ_ID = r.RNT_EQ
           JOIN models m ON m.MOD_ID = eq.EQ_MOD
           JOIN categories c ON c.CAT_ID = m.MOD_CAT
          GROUP BY model, category ORDER BY cnt DESC LIMIT 10",
    'Поступления по филиалам' =>
        "SELECT b.BR_ID AS branch, COUNT(DISTINCT ctr.CTR_ID) AS contracts,
                ROUND(SUM(p.PAY_AMOUNT),2) AS amount
           FROM payments p
           JOIN contracts ctr ON ctr.CTR_ID = p.PAY_CTR
           JOIN requests rq ON rq.REQ_ID = ctr.CTR_REQ
           JOIN branches b ON b.BR_ID = rq.REQ_BR
          GROUP BY b.BR_ID ORDER BY amount DESC",
    'Заявки по статусам' =>
        "SELECT rs.RST_NAME AS status, COUNT(*) AS cnt, ROUND(SUM(rq.REQ_SUM),2) AS amount
           FROM requests rq JOIN request_statuses rs ON rs.RST_ID = rq.REQ_STATUS
          GROUP BY rs.RST_NAME ORDER BY cnt DESC",
    'Структура парка по категориям' =>
        "SELECT c.CAT_NAME AS category, COUNT(*) AS units,
                SUM(eq.EQ_STATUS='аренда') AS rented
           FROM equipment_units eq
           JOIN models m ON m.MOD_ID = eq.EQ_MOD
           JOIN categories c ON c.CAT_ID = m.MOD_CAT
          GROUP BY c.CAT_NAME ORDER BY units DESC",
    'Затраты на обслуживание и ремонт' =>
        "SELECT mt.MT_NAME AS work, COUNT(*) AS cnt, ROUND(SUM(mn.MNT_COST),2) AS cost
           FROM maintenance mn JOIN maintenance_types mt ON mt.MT_ID = mn.MNT_TYPE
          GROUP BY mt.MT_NAME ORDER BY cost DESC",
    'ВУЗы-должники' => 'SELECT * FROM v_debtors ORDER BY OVERDUE_ITEMS DESC LIMIT 20',
    'Перемещения техники' =>
        "SELECT t.TR_DATE, t.TR_FROM, t.TR_TO, eq.EQ_INV, t.TR_REASON
           FROM transfers t JOIN equipment_units eq ON eq.EQ_ID = t.TR_EQ
          ORDER BY t.TR_DATE DESC LIMIT 40",
];

$selected = $_GET['r'] ?? array_key_first($reports);
$rows = [];
$error = null;
if (isset($reports[$selected])) {
    try {
        $rows = db()->query($reports[$selected])->fetchAll();
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}
?>
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Отчёты — CampusRent</title>
  <style>
    body { font-family:-apple-system,"Segoe UI",Arial,sans-serif; margin:0; background:#f7f8fa; }
    header { background:#1e3a8a; color:#fff; padding:16px 28px; }
    header a { color:#bfdbfe; text-decoration:none; font-size:13px; }
    header h1 { margin:6px 0 0; font-size:19px; }
    main { padding:20px 28px 60px; }
    nav a { display:inline-block; margin:0 8px 8px 0; padding:7px 12px; background:#eff6ff;
            border:1px solid #dbeafe; border-radius:8px; color:#1e3a8a; text-decoration:none; font-size:13px; }
    nav a.active { background:#1e3a8a; color:#fff; }
    table { border-collapse:collapse; background:#fff; font-size:13px; }
    th, td { border:1px solid #e5e7eb; padding:6px 10px; text-align:left; }
    th { background:#f3f4f6; }
    .err { background:#fee2e2; border:1px solid #fca5a5; color:#991b1b; padding:10px 14px; border-radius:8px; }
  </style>
</head>
<body>
<header>
  <a href="index.php">← главное меню</a>
  <h1>Отчётные формы</h1>
</header>
<main>
  <nav>
    <?php foreach (array_keys($reports) as $name): ?>
      <a class="<?= $name === $selected ? 'active' : '' ?>"
         href="reports.php?r=<?= urlencode($name) ?>"><?= h($name) ?></a>
    <?php endforeach; ?>
  </nav>
  <?php if ($error): ?><div class="err"><?= h($error) ?></div><?php endif; ?>
  <table>
    <?php if ($rows): ?>
      <tr><?php foreach (array_keys($rows[0]) as $c): ?><th><?= h($c) ?></th><?php endforeach; ?></tr>
      <?php foreach ($rows as $r): ?>
        <tr><?php foreach ($r as $v): ?><td><?= h((string)$v) ?></td><?php endforeach; ?></tr>
      <?php endforeach; ?>
    <?php else: ?>
      <tr><td>Нет данных</td></tr>
    <?php endif; ?>
  </table>
</main>
</body>
</html>
