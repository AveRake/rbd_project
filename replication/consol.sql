-- Пользователь репликации на узле консолидации
CREATE USER IF NOT EXISTS 'replconsol'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
GRANT REPLICATION SLAVE ON *.* TO 'replconsol'@'%';
FLUSH PRIVILEGES;
