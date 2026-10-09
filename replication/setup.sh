#!/usr/bin/env bash
# =====================================================================
#  CampusRent — развёртывание стенда репликации.
#  Требуется: docker + docker compose.
#
#  Использование:  ./setup.sh
# =====================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MY="mysql -uroot -ppassword --default-character-set=utf8mb4"

echo "==> 1. Запуск контейнеров"
docker compose up -d

echo "==> 2. Ожидание готовности узлов"
for svc in mysql-master mysql-slave mysql-slave2 mysql-consol; do
  printf "    %s" "$svc"
  for i in $(seq 1 60); do
    if docker exec "$svc" mysqladmin ping -uroot -ppassword --silent >/dev/null 2>&1; then
      echo " — готов"; break
    fi
    printf "."; sleep 2
  done
done

echo "==> 3. Загрузка схемы и данных во все узлы"
for svc in mysql-master mysql-slave mysql-slave2 mysql-consol; do
  echo "    --> $svc"
  for f in 01_schema.sql 02_reference_data.sql; do
    docker exec -i "$svc" $MY < "$ROOT/sql/$f"
  done
done

echo "==> 4. Настройка каналов репликации"
# РОК: ЦО -> филиалы
for svc in mysql-slave mysql-slave2; do
  docker exec -i "$svc" $MY <<'SQL'
CHANGE MASTER TO
  MASTER_HOST='mysql-master',
  MASTER_USER='repl',
  MASTER_PASSWORD='password',
  GET_MASTER_PUBLIC_KEY=1;
START SLAVE;
SQL
done

# РКД: филиалы -> узел консолидации
docker exec -i mysql-consol $MY <<'SQL'
CHANGE MASTER TO MASTER_HOST='mysql-master', MASTER_USER='repl',
  MASTER_PASSWORD='password', GET_MASTER_PUBLIC_KEY=1 FOR CHANNEL 'hq';
CHANGE MASTER TO MASTER_HOST='mysql-slave', MASTER_USER='replslave',
  MASTER_PASSWORD='password', GET_MASTER_PUBLIC_KEY=1 FOR CHANNEL 'spb';
CHANGE MASTER TO MASTER_HOST='mysql-slave2', MASTER_USER='replslave',
  MASTER_PASSWORD='password', GET_MASTER_PUBLIC_KEY=1 FOR CHANNEL 'kzn';
START SLAVE FOR CHANNEL 'hq';
START SLAVE FOR CHANNEL 'spb';
START SLAVE FOR CHANNEL 'kzn';
SQL

echo "==> 5. Загрузка тестовых данных на узел ЦО"
for f in 03_test_data.sql 04_views.sql 05_triggers.sql 06_indexes.sql 07_users_grants.sql; do
  docker exec -i mysql-master $MY < "$ROOT/sql/$f"
done

echo "==> 6. Состояние репликации"
docker exec mysql-slave  $MY -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Master_Host"
docker exec mysql-consol $MY -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Channel_Name"

echo "Готово."
