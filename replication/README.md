# Настройка репликации (стенд на Docker)

## Состав узлов

| Контейнер | Роль | Порт на хосте | server-id |
|---|---|---|---|
| `mysql-master` | Центральный офис (источник НСИ) | 3306 | 1 |
| `mysql-slave` | Филиал Санкт-Петербург | 3307 | 2 |
| `mysql-slave2` | Филиал Казань | 3309 | 4 |
| `mysql-consol` | Узел консолидации | 3308 | 3 |

## Быстрый запуск

```bash
cd replication
./setup.sh          # поднимает контейнеры и настраивает репликацию
```

Либо вручную:

```bash
docker compose up -d
# далее см. шаги в setup.sh
```

## Ручная проверка репликации

**1. Репликация с основной копией (РОК) — НСИ из ЦО в филиалы.**
```bash
docker exec -it mysql-master mysql -uroot -ppassword campusrent -e \
  "UPDATE tariffs SET TAR_PRICE = TAR_PRICE + 100 WHERE TAR_ID = 2011;"
docker exec -it mysql-slave  mysql -uroot -ppassword campusrent -e \
  "SELECT TAR_ID, TAR_PRICE FROM tariffs WHERE TAR_ID = 2011;"
```
Изменение, сделанное на master, должно появиться на slave.

**2. Репликация без основной копии (РБОК) — клиенты.**
```bash
docker exec -it mysql-slave mysql -uroot -ppassword campusrent -e \
  "INSERT INTO universities (UN_ID,UN_NAME,UN_SHORT,UN_INN,UN_ADDRESS,UN_CITY,UN_BR)
   VALUES (9099,'Тестовый университет','ТЕСТВУЗ','9900000099','ул. Тестовая, 1','Москва','HQ');"
docker exec -it mysql-master mysql -uroot -ppassword campusrent -e \
  "SELECT UN_ID, UN_SHORT FROM universities WHERE UN_ID = 9099;"
```
Запись, добавленная в филиале, должна появиться в ЦО.

**3. Репликация с консолидацией (РКД).**
```bash
docker exec -it mysql-slave mysql -uroot -ppassword campusrent -e \
  "INSERT INTO equipment_units (EQ_ID,EQ_INV,EQ_MOD,EQ_BR,EQ_STATUS,EQ_COND,EQ_ACQUIRE)
   VALUES (909900,'SPB-909900',201,'SPB','свободна',2,'2026-09-01');"
docker exec -it mysql-consol mysql -uroot -ppassword campusrent -e \
  "SELECT EQ_ID, EQ_INV, EQ_BR FROM equipment_units WHERE EQ_ID = 909900;"
```
Запись из филиала должна появиться в консолидированной копии.

**4. Состояние репликации.**
```bash
docker exec -it mysql-slave  mysql -uroot -ppassword -e "SHOW SLAVE STATUS\G" | grep -E "Running|Master_Host"
docker exec -it mysql-consol mysql -uroot -ppassword -e "SHOW SLAVE STATUS\G" | grep -E "Running|Channel_Name"
```
Ожидается `Slave_IO_Running: Yes` и `Slave_SQL_Running: Yes`.

## Примечания

- В MySQL 8.4 команда `CHANGE MASTER TO` заменена на
  `CHANGE REPLICATION SOURCE TO ... SOURCE_HOST=...`; скрипты даны для MySQL 8.0
  (образ `mysql:8.0`), как в методических указаниях.
- Конфигурационные файлы монтируются в `/etc/mysql/conf.d/`, чтобы не
  переопределять базовые настройки образа целиком.
- Консолидированная копия содержит не все таблицы, поэтому ограничения
  `FOREIGN KEY` на отсутствующие таблицы в консолидированной БД снимаются
  (поля при этом сохраняются). См. `docs/06_Реализация_репликации.md`, п. 6.5.
- Для остановки и удаления стенда: `docker compose down -v`.
