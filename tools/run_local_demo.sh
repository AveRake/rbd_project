#!/usr/bin/env bash
# =====================================================================
#  CampusRent — локальный прогон проекта на одном сервере MySQL.
#
#  Использование:
#     tools/run_local_demo.sh "-h 127.0.0.1 -P 3306 -uroot -pSECRET"
#
#  Скрипт:
#    1) создаёт БД и таблицы, загружает НСИ и тестовые данные;
#    2) создаёт представления, триггеры, индексы, роли и права;
#    3) выполняет отчётные запросы и сохраняет результат;
#    4) прогоняет тесты ограничений целостности и сохраняет результат.
# =====================================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MYSQL_ARGS="${1:--uroot}"
RES="$ROOT/results"
mkdir -p "$RES"

run_sql() {
  local file="$1"
  echo "==> $file"
  mysql $MYSQL_ARGS --default-character-set=utf8mb4 < "$file"
}

run_sql "$ROOT/sql/01_schema.sql"
run_sql "$ROOT/sql/02_reference_data.sql"
run_sql "$ROOT/sql/03_test_data.sql"
run_sql "$ROOT/sql/04_views.sql"
run_sql "$ROOT/sql/05_triggers.sql"
run_sql "$ROOT/sql/06_indexes.sql"
run_sql "$ROOT/sql/07_users_grants.sql"

echo "==> отчётные запросы"
mysql $MYSQL_ARGS --default-character-set=utf8mb4 --table \
  < "$ROOT/sql/08_queries.sql" > "$RES/query_results.txt"
echo "   результат: $RES/query_results.txt"

echo "==> тесты ограничений целостности"
mysql $MYSQL_ARGS --default-character-set=utf8mb4 --table --force \
  < "$ROOT/tools/integrity_tests.sql" > "$RES/integrity_tests.txt" 2>&1
echo "   результат: $RES/integrity_tests.txt"

echo "Готово."
