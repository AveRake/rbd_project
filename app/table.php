<?php
// CampusRent — просмотр и редактирование таблицы (универсальная форма).
require __DIR__ . '/config.php';

$table = $_GET['t'] ?? 'equipment_units';

/** Разрешённые к просмотру таблицы и представления. */
$allowed = array_merge(
    ['v_available_equipment', 'v_current_rentals', 'v_overdue_rentals',
     'v_branch_load', 'v_consolidated_fleet', 'v_debtors', 'v_request_full'],
    array_merge(...array_values(table_groups()))
);
if (!in_array($table, $allowed, true)) {
    http_response_code(400);
    exit('Недопустимая таблица');
}

$isView = str_starts_with($table, 'v_');
$message = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && !$isView) {
    try {
        if (($_POST['action'] ?? '') === 'delete') {
            $cols = db()->query("SHOW KEYS FROM `$table` WHERE Key_name = 'PRIMARY'")->fetchAll();
            if ($cols) {
                $where = [];
                $args = [];
                foreach ($cols as $c) {
                    $where[] = "`{$c['Column_name']}` = ?";
                    $args[] = $_POST['pk_' . $c['Column_name']] ?? null;
                }
                $st = db()->prepare("DELETE FROM `$table` WHERE " . implode(' AND ', $where));
                $st->execute($args);
                $message = 'Запись удалена';
            }
        } elseif (($_POST['action'] ?? '') === 'insert') {
            $cols = db()->query("SHOW COLUMNS FROM `$table`")->fetchAll();
            $names = [];
            $marks = [];
            $args  = [];
            foreach ($cols as $c) {
                $name = $c['Field'];
                if (stripos($c['Extra'], 'auto_increment') !== false) {
                    continue;
                }
                if (!isset($_POST['f_' . $name]) || $_POST['f_' . $name] === '') {
                    continue;
                }
                $names[] = "`$name`";
                $marks[] = '?';
                $args[]  = $_POST['f_' . $name];
            }
            if ($names) {
                $sql = "INSERT INTO `$table` (" . implode(',', $names) . ") VALUES (" .
                       implode(',', $marks) . ")";
                db()->prepare($sql)->execute($args);
                $message = 'Запись добавлена';
            } else {
                $error = 'Не заполнено ни одно поле';
            }
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

$limit = 100;
$rows = [];
$cols = [];
$pkCols = [];
try {
    $rows = db()->query("SELECT * FROM `$table` LIMIT $limit")->fetchAll();
    $cols = db()->query("SHOW COLUMNS FROM `$table`")->fetchAll();
    $pkCols = db()->query("SHOW KEYS FROM `$table` WHERE Key_name = 'PRIMARY'")->fetchAll();
} catch (Throwable $e) {
    $error = $e->getMessage();
}
$pkNames = array_column($pkCols, 'Column_name');
?>
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title><?= h(table_title($table)) ?> — CampusRent</title>
  <style>
    body { font-family:-apple-system,"Segoe UI",Arial,sans-serif; margin:0; background:#f7f8fa; color:#111827; }
    header { background:#1e3a8a; color:#fff; padding:16px 28px; }
    header a { color:#bfdbfe; text-decoration:none; font-size:13px; }
    header h1 { margin:6px 0 0; font-size:19px; }
    main { padding:20px 28px 60px; }
    table { border-collapse:collapse; background:#fff; font-size:13px; }
    th, td { border:1px solid #e5e7eb; padding:6px 9px; text-align:left; white-space:nowrap; }
    th { background:#f3f4f6; position:sticky; top:0; }
    .wrap { overflow:auto; max-height:62vh; border:1px solid #e5e7eb; border-radius:8px; }
    .msg { background:#dcfce7; border:1px solid #86efac; color:#166534; padding:10px 14px; border-radius:8px; margin-bottom:12px; }
    .err { background:#fee2e2; border:1px solid #fca5a5; color:#991b1b; padding:10px 14px; border-radius:8px; margin-bottom:12px; }
    form.add { background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:14px; margin-top:16px; }
    form.add label { display:inline-block; font-size:12px; color:#374151; margin:4px 8px 4px 0; }
    form.add input { border:1px solid #d1d5db; border-radius:6px; padding:5px 7px; font-size:13px; width:150px; }
    button { border:0; border-radius:6px; padding:6px 12px; font-size:13px; cursor:pointer; }
    .del { background:#fee2e2; color:#991b1b; }
    .add-btn { background:#1e3a8a; color:#fff; margin-top:10px; }
    .note { font-size:12px; color:#6b7280; margin:10px 0; }
  </style>
</head>
<body>
<header>
  <a href="index.php">← главное меню</a>
  <h1><?= h(table_title($table)) ?> <span style="font-weight:400;font-size:13px">(<?= h($table) ?>)</span></h1>
</header>
<main>
  <?php if ($message): ?><div class="msg"><?= h($message) ?></div><?php endif; ?>
  <?php if ($error): ?><div class="err"><?= h($error) ?></div><?php endif; ?>

  <?php if ($isView): ?>
    <div class="note">Представление доступно только для чтения.</div>
  <?php endif; ?>

  <div class="wrap">
    <table>
      <tr>
        <?php foreach ($cols as $c): ?><th><?= h($c['Field']) ?></th><?php endforeach; ?>
        <?php if (!$isView): ?><th></th><?php endif; ?>
      </tr>
      <?php foreach ($rows as $r): ?>
        <tr>
          <?php foreach ($cols as $c): ?>
            <td><?= h((string)($r[$c['Field']] ?? '')) ?></td>
          <?php endforeach; ?>
          <?php if (!$isView): ?>
            <td>
              <?php if ($pkNames): ?>
              <form method="post" onsubmit="return confirm('Удалить запись?')">
                <input type="hidden" name="action" value="delete">
                <?php foreach ($pkNames as $pk): ?>
                  <input type="hidden" name="pk_<?= h($pk) ?>" value="<?= h((string)$r[$pk]) ?>">
                <?php endforeach; ?>
                <button class="del" type="submit">удалить</button>
              </form>
              <?php endif; ?>
            </td>
          <?php endif; ?>
        </tr>
      <?php endforeach; ?>
    </table>
  </div>
  <div class="note">Показано не более <?= $limit ?> записей. Внешние ключи должны
    ссылаться на существующие записи; ограничения целостности проверяются триггерами.</div>

  <?php if (!$isView): ?>
  <form class="add" method="post">
    <input type="hidden" name="action" value="insert">
    <b style="font-size:14px">Добавить запись</b><br>
    <?php foreach ($cols as $c):
        if (stripos($c['Extra'], 'auto_increment') !== false) continue; ?>
      <label><?= h($c['Field']) ?> <small>(<?= h($c['Type']) ?><?= $c['Null']==='NO' ? ', обяз.' : '' ?>)</small><br>
        <input name="f_<?= h($c['Field']) ?>" placeholder="<?= h($c['Field']) ?>"></label>
    <?php endforeach; ?>
    <br><button class="add-btn" type="submit">добавить</button>
  </form>
  <?php endif; ?>
</main>
</body>
</html>
