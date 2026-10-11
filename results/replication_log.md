# Протокол проверки репликации

Стенд: MySQL 8.0 в Docker (`replication/setup.sh`), четыре узла —
`mysql-master` (ЦО), `mysql-slave` (СПб), `mysql-slave2` (Казань),
`mysql-consol` (консолидация).

Дата проверки: 11.10.2026. Стенд пересобран начисто командой
`docker compose down -v && bash setup.sh`.

## 1. Запуск стенда и состояние каналов

`bash setup.sh` поднял 4 контейнера, загрузил одинаковый снимок `sql/01…07`
во все узлы, зафиксировал позиции бинарных журналов и включил **шесть
каналов** репликации.

| Узел | Канал | Источник | `Slave_IO_Running` | `Slave_SQL_Running` | `Last_Error` |
|---|---|---|---|---|---|
| `mysql-slave` | — | `mysql-master` | Yes | Yes | пусто |
| `mysql-slave2` | — | `mysql-master` | Yes | Yes | пусто |
| `mysql-master` | — | `mysql-slave` | Yes | Yes | пусто |
| `mysql-consol` | `hq` | `mysql-master` | Yes | Yes | пусто |
| `mysql-consol` | `spb` | `mysql-slave` | Yes | Yes | пусто |
| `mysql-consol` | `kzn` | `mysql-slave2` | Yes | Yes | пусто |

## 2. Проверка методов поддержки распределённости

| № | Метод | Что сделано | Ожидаемый результат | Факт |
|---|---|---|---|---|
| 1 | **РОК** (с основной копией) | `UPDATE tariffs SET TAR_PRICE = TAR_PRICE + 100 WHERE TAR_ID = 2011` на ЦО | изменение появилось в обоих филиалах | **подтверждено**: `TAR_PRICE = 844.00` на `mysql-master`, `mysql-slave` и `mysql-slave2` |
| 2 | **РБОК** (без основной копии) | `INSERT` вуза `UN_ID=9099` в филиале СПб | запись появилась в ЦО **и в другом филиале** | **подтверждено**: вуз `ТЕСТВУЗ` найден на `mysql-master` и на `mysql-slave2` |
| 3 | **РКД** (консолидация) | `INSERT` экземпляра `EQ_ID=909900` в филиале СПб | запись появилась в консолидированной копии | **подтверждено**: `SPB-909900` (`EQ_BR=SPB`) найден на `mysql-consol` |
| 4 | **Распределённая транзакция РТ-1** | `bash distributed_booking.sh` | бронирование атомарно на двух узлах | **подтверждено**: см. `distributed_booking_log.md` |
| 5 | Состояние каналов после всех проверок | `SHOW SLAVE STATUS` | все каналы Yes, без ошибок | **подтверждено**: 6 из 6 каналов Yes, `Last_Error` пусто |

Тестовые записи (вуз `9099`, экземпляр `909900`) после проверки удалены;
контроль: `universities/equipment_units` на ЦО → `0/0`.

## 3. Что было обнаружено и исправлено в ходе проверки

1. **`log_replica_updates` в MySQL 8.0 включён по умолчанию.** Проверено:
   `SELECT @@log_replica_updates` → `1` на всех четырёх узлах. Именно поэтому
   РБОК доходит до второго филиала транзитом через ЦО (п. 2, строка 2).
   Прежняя версия протокола предполагала, что параметр выключен, и описывала
   распространение только до ЦО.
2. **DDL-скрипты нельзя повторно запускать на отдельном узле работающего
   стенда.** Созданный объект попадает в бинарный журнал, разносится по
   каналам, и узел, где такой объект уже есть, останавливает канал с ошибкой
   `1304 ... already exists`. Это наблюдалось при повторном прогоне
   `sql/06_indexes.sql` на узле ЦО: остановились канал РБОК на `mysql-master`
   и канал `spb` на `mysql-consol`. В `sql/06_indexes.sql`,
   `replication/setup.sh` и `docs/06_Реализация_репликации.md` добавлено
   соответствующее предупреждение.
3. **XA-транзакции несовместимы с фильтрами репликации.** При попытке
   применить XA-транзакцию на узле, фильтр которого исключает её таблицы,
   канал останавливается с ошибкой `3898 — The use of replication filters with
   XA transactions is not supported`. Это определило выбор узлов в
   `distributed_booking.sh` (см. `distributed_booking_log.md`, разд. «Ограничения»).
4. **Узел консолидации собирал только один филиал.** В `setup.sh` было два
   канала (`hq`, `spb`), то есть данные Казани в консолидированную копию не
   попадали. Добавлен третий канал `kzn`; теперь консолидируются оба филиала.

## 4. Команды для воспроизведения

```bash
cd replication
docker compose down -v      # чистое состояние
bash setup.sh               # 2–4 минуты

# состояние каналов
docker exec mysql-slave  mysql -uroot -ppassword --default-character-set=utf8mb4 \
  -e "SHOW SLAVE STATUS\G" | grep -E "Master_Host|Running|Last_Error"
docker exec mysql-consol mysql -uroot -ppassword --default-character-set=utf8mb4 \
  -e "SHOW SLAVE STATUS\G" | grep -E "Channel_Name|Master_Host|Running|Last_Error"

# распределённая транзакция
bash distributed_booking.sh
```

Параметр `--default-character-set=utf8mb4` обязателен: в образе локаль `C`,
без него клиент переключается на `latin1` и вставка в `VARCHAR(12)`
(`EQ_STATUS`) падает с ошибкой `1406`.

## 5. Полный вывод

Дословный вывод проверок сохранён в `replication_log.txt` (проверки репликации)
и `distributed_booking_log.txt` (распределённая транзакция).
