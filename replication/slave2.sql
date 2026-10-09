-- Пользователь репликации на узле филиала Казань
CREATE USER IF NOT EXISTS 'replslave'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
GRANT REPLICATION SLAVE ON *.* TO 'replslave'@'%';
FLUSH PRIVILEGES;
