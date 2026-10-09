<?php
// CampusRent — главное меню демонстрационного приложения.
require __DIR__ . '/config.php';

$node = cfg('DB_HOST', '127.0.0.1') . ':' . cfg('DB_PORT', '3306');
$error = null;
$info = null;
try {
    $info = db()->query('SELECT VERSION() AS v')->fetch();
    $counts = db()->query(
        'SELECT (SELECT COUNT(*) FROM equipment_units) AS eq,
                (SELECT COUNT(*) FROM requests) AS rq,
                (SELECT COUNT(*) FROM contracts) AS ct,
                (SELECT COUNT(*) FROM rentals) AS rn'
    )->fetch();
} catch (Throwable $e) {
    $error = $e->getMessage();
}
?>
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CampusRent — РАИС аренды техники</title>
  <style>
    body { font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 0; background:#f7f8fa; color:#111827; }
    header { background:#1e3a8a; color:#fff; padding:22px 32px; }
    header h1 { margin:0 0 4px; font-size:22px; }
    header .sub { opacity:.85; font-size:13px; }
    main { padding:24px 32px 60px; }
    .card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:18px 20px; margin-bottom:18px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:10px; }
    a.tile { display:block; padding:12px 14px; border:1px solid #dbeafe; border-radius:8px;
             text-decoration:none; color:#1e3a8a; background:#eff6ff; font-size:14px; }
    a.tile:hover { background:#dbeafe; }
    h2 { font-size:16px; margin:0 0 12px; color:#374151; }
    .badge { display:inline-block; background:#dcfce7; color:#166534; border-radius:6px;
             padding:2px 8px; font-size:12px; margin-right:6px; }
    .err { background:#fee2e2; border:1px solid #fca5a5; color:#991b1b; padding:12px; border-radius:8px; }
    .stats span { margin-right:18px; font-size:14px; }
  </style>
</head>
<body>
<header>
  <h1>CampusRent — сервис аренды техники для высших учебных заведений</h1>
  <div class="sub">Распределённая автоматизированная информационная система · узел <?= h($node) ?></div>
</header>
<main>
  <?php if ($error): ?>
    <div class="err"><b>Нет соединения с БД:</b> <?= h($error) ?><br>
      Проверьте настройки подключения (переменные окружения DB_HOST, DB_PORT, DB_USER, DB_PASS).</div>
  <?php else: ?>
    <div class="card">
      <span class="badge">MySQL <?= h($info['v']) ?></span>
      <span class="badge">БД <?= h(DB_NAME) ?></span>
      <div class="stats" style="margin-top:10px">
        <span>Экземпляров техники: <b><?= h($counts['eq']) ?></b></span>
        <span>Заявок: <b><?= h($counts['rq']) ?></b></span>
        <span>Договоров: <b><?= h($counts['ct']) ?></b></span>
        <span>Выдач: <b><?= h($counts['rn']) ?></b></span>
      </div>
    </div>

    <div class="card">
      <h2>Отчётные формы</h2>
      <div class="grid">
        <a class="tile" href="reports.php">📊 Отчёты и сводки</a>
        <a class="tile" href="table.php?t=v_available_equipment">🟢 Свободная техника</a>
        <a class="tile" href="table.php?t=v_current_rentals">📦 Текущие выдачи</a>
        <a class="tile" href="table.php?t=v_overdue_rentals">⏰ Просроченные возвраты</a>
      </div>
    </div>

    <?php foreach (table_groups() as $group => $tables): ?>
      <div class="card">
        <h2><?= h($group) ?></h2>
        <div class="grid">
          <?php foreach ($tables as $t): ?>
            <a class="tile" href="table.php?t=<?= urlencode($t) ?>"><?= h(table_title($t)) ?></a>
          <?php endforeach; ?>
        </div>
      </div>
    <?php endforeach; ?>
  <?php endif; ?>
</main>
</body>
</html>
