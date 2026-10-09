-- Пользователь репликации на узле филиала СПб
-- (нужен, потому что таблицы клиентов реплицируются в обе стороны — РБОК)
CREATE USER IF NOT EXISTS 'replslave'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
GRANT REPLICATION SLAVE ON *.* TO 'replslave'@'%';
FLUSH PRIVILEGES;
