<?php
// =====================================================================
//  CampusRent — общие настройки демонстрационного веб-приложения.
//  Параметры подключения можно переопределить переменными окружения,
//  что позволяет переключаться между узлами РБД (ЦО / филиалы).
// =====================================================================

function cfg(string $key, string $default): string
{
    $v = getenv($key);
    return ($v === false || $v === '') ? $default : $v;
}

const DB_NAME = 'campusrent';

/** Роль узла по номеру порта: чтобы на экране было видно, какая база открыта. */
function node_role(): string
{
    $roles = [
        '3306' => 'центральный офис (основная копия НСИ)',
        '3307' => 'филиал Санкт-Петербург',
        '3308' => 'узел консолидации (сводная копия)',
        '3309' => 'филиал Казань',
    ];
    $port = cfg('DB_PORT', '3306');
    return $roles[$port] ?? 'внешний узел';
}

/** Подпись узла для шапки страницы: адрес, порт и роль. */
function node_caption(): string
{
    return cfg('DB_HOST', '127.0.0.1') . ':' . cfg('DB_PORT', '3306')
        . ' — ' . node_role();
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $host = cfg('DB_HOST', '127.0.0.1');
        $port = cfg('DB_PORT', '3306');
        $user = cfg('DB_USER', 'root');
        $pass = cfg('DB_PASS', 'password');
        $dsn  = "mysql:host=$host;port=$port;dbname=" . DB_NAME . ";charset=utf8mb4";
        $pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
    }
    return $pdo;
}

/** Человекочитаемое название таблицы. */
function table_title(string $t): string
{
    $map = [
        'branches' => 'Филиалы', 'categories' => 'Категории техники',
        'models' => 'Модели техники', 'model_components' => 'Комплектация моделей',
        'model_purposes' => 'Назначение моделей', 'tariffs' => 'Тарифы',
        'request_statuses' => 'Статусы заявок', 'payment_methods' => 'Способы оплаты',
        'maintenance_types' => 'Виды работ', 'condition_grades' => 'Степени состояния',
        'employees' => 'Сотрудники', 'universities' => 'ВУЗы',
        'departments' => 'Подразделения', 'representatives' => 'Представители',
        'equipment_units' => 'Экземпляры техники', 'transfers' => 'Перемещения техники',
        'requests' => 'Заявки на аренду', 'request_items' => 'Позиции заявок',
        'contracts' => 'Договоры аренды', 'rentals' => 'Выдачи техники',
        'payments' => 'Платежи', 'maintenance' => 'Обслуживание и ремонт',
    ];
    return $map[$t] ?? $t;
}

/** Группы таблиц для главного меню. */
function table_groups(): array
{
    return [
        'Номенклатура и тарифы' => ['categories', 'models', 'model_components',
            'model_purposes', 'tariffs'],
        'Клиенты' => ['universities', 'departments', 'representatives'],
        'Техника' => ['equipment_units', 'transfers'],
        'Аренда' => ['requests', 'request_items', 'contracts', 'rentals', 'payments'],
        'Сервис и персонал' => ['maintenance', 'employees'],
        'Справочники' => ['branches', 'request_statuses', 'payment_methods',
            'maintenance_types', 'condition_grades'],
    ];
}

function h($s): string
{
    return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
