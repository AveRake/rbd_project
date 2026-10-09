#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — генератор тестовых данных.

Формирует файл sql/03_test_data.sql с реалистичным набором данных:
вузы, подразделения, представители, экземпляры техники, заявки, позиции,
договоры, выдачи, платежи, обслуживание и перемещения.

Генерация детерминированная (фиксированное зерно), поэтому данные и
результаты запросов воспроизводимы при повторном запуске.

Запуск:  python3 tools/gen_data.py
"""

import os
import random
from datetime import date, timedelta

random.seed(20251009)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sql", "03_test_data.sql")

# Дата-«якорь», относительно которой строится набор данных (снимок на 09.10.2026).
ANCHOR = date(2026, 10, 9)

# ------------------------------------------------------------------------
# Вспомогательные средства
# ------------------------------------------------------------------------


def q(v):
    """Экранирование строкового значения для SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, date):
        return "'%s'" % v.isoformat()
    return "'%s'" % str(v).replace("\\", "\\\\").replace("'", "''")


def insert(table, columns, rows, chunk=200):
    """Формирует SQL-инструкции INSERT ... VALUES пачками."""
    out = []
    if not rows:
        return out
    cols = ", ".join(columns)
    for i in range(0, len(rows), chunk):
        part = rows[i:i + chunk]
        values = ",\n  ".join("(" + ", ".join(q(x) for x in r) + ")" for r in part)
        out.append("INSERT INTO %s (%s) VALUES\n  %s;" % (table, cols, values))
    return out


def d(days_from, days_to):
    """Случайная дата в окне относительно ANCHOR."""
    return ANCHOR + timedelta(days=random.randint(days_from, days_to))


# ------------------------------------------------------------------------
# 1. Университеты
# ------------------------------------------------------------------------

UNIV = {
    "HQ": [
        ("МГУ", "Московский государственный университет имени М. В. Ломоносова"),
        ("МГТУ", "Московский государственный технический университет имени Н. Э. Баумана"),
        ("НИУ ВШЭ", "Национальный исследовательский университет «Высшая школа экономики»"),
        ("МИФИ", "Национальный исследовательский ядерный университет «МИФИ»"),
        ("МАИ", "Московский авиационный институт"),
        ("МЭИ", "Национальный исследовательский университет «МЭИ»"),
        ("МИРЭА", "МИРЭА — Российский технологический университет"),
        ("РУДН", "Российский университет дружбы народов"),
        ("МПГУ", "Московский педагогический государственный университет"),
        ("МГСУ", "Московский государственный строительный университет"),
        ("ГУУ", "Государственный университет управления"),
        ("МФТИ", "Московский физико-технический институт"),
    ],
    "SPB": [
        ("СПбГУ", "Санкт-Петербургский государственный университет"),
        ("СПбПУ", "Санкт-Петербургский политехнический университет Петра Великого"),
        ("ИТМО", "Национальный исследовательский университет ИТМО"),
        ("СПбГМТУ", "Санкт-Петербургский государственный морской технический университет"),
        ("ЛЭТИ", "Санкт-Петербургский государственный электротехнический университет «ЛЭТИ»"),
        ("ПГУПС", "Петербургский государственный университет путей сообщения"),
        ("СПбГАСУ", "Санкт-Петербургский государственный архитектурно-строительный университет"),
        ("РГПУ", "Российский государственный педагогический университет имени А. И. Герцена"),
        ("СПбГУПТД", "Санкт-Петербургский государственный университет промышленных технологий и дизайна"),
        ("ВШТЭ", "Высшая школа технологии и энергетики"),
        ("СЗИУ", "Северо-Западный институт управления РАНХиГС"),
        ("ГУАП", "Санкт-Петербургский государственный университет аэрокосмического приборостроения"),
    ],
    "KZN": [
        ("КФУ", "Казанский (Приволжский) федеральный университет"),
        ("КНИТУ", "Казанский национальный исследовательский технологический университет"),
        ("КГЭУ", "Казанский государственный энергетический университет"),
        ("КНИТУ-КАИ", "Казанский национальный исследовательский технический университет имени А. Н. Туполева"),
        ("КГАСУ", "Казанский государственный архитектурно-строительный университет"),
        ("КГМУ", "Казанский государственный медицинский университет"),
        ("ПГТУ", "Поволжский государственный технологический университет"),
        ("КИУ", "Казанский инновационный университет"),
        ("УлГУ", "Ульяновский государственный университет"),
    ],
    "NSK": [
        ("НГУ", "Новосибирский национальный исследовательский государственный университет"),
        ("НГТУ", "Новосибирский государственный технический университет"),
        ("НГУЭУ", "Новосибирский государственный университет экономики и управления"),
        ("СГУГиТ", "Сибирский государственный университет геосистем и технологий"),
        ("НГАУ", "Новосибирский государственный аграрный университет"),
        ("СибГУТИ", "Сибирский государственный университет телекоммуникаций и информатики"),
        ("НГМУ", "Новосибирский государственный медицинский университет"),
        ("НГАСУ", "Новосибирский государственный архитектурно-строительный университет"),
        ("ТГУ", "Томский государственный университет"),
    ],
}

CITY = {"HQ": "Москва", "SPB": "Санкт-Петербург", "KZN": "Казань", "NSK": "Новосибирск"}
STREET = ["ул. Университетская", "пр. Науки", "ул. Студенческая", "наб. Реки", "ул. Победы",
          "пр. Ленина", "ул. Академическая", "ул. Мира", "ул. Гагарина", "пр. Строителей"]
EMAIL_DOM = {"HQ": "msk", "SPB": "spb", "KZN": "kzn", "NSK": "nsk"}

universities = []           # (un_id, name, short, inn, kpp, addr, city, phone, email, br)
un_by_branch = {b: [] for b in UNIV}
un_id = 1001
for br in ["HQ", "SPB", "KZN", "NSK"]:
    for short, name in UNIV[br]:
        inn = "77%08d" % (un_id - 1000 + 100)
        kpp = "77%07d" % (un_id - 1000 + 500)
        addr = "%s, д. %d" % (random.choice(STREET), random.randint(1, 60))
        phone = "+7 %s %03d-%02d-%02d" % (
            {"HQ": "495", "SPB": "812", "KZN": "843", "NSK": "383"}[br],
            random.randint(100, 999), random.randint(10, 99), random.randint(10, 99))
        email = "office%d@%s.edu.ru" % (un_id, EMAIL_DOM[br])
        universities.append((un_id, name, short, inn, kpp, addr, CITY[br], phone, email, br))
        un_by_branch[br].append(un_id)
        un_id += 1

# ------------------------------------------------------------------------
# 2. Подразделения университетов
# ------------------------------------------------------------------------

DEP_KINDS = ["Факультет", "Кафедра", "Лаборатория", "Институт", "Учебный центр"]
DEP_TOPICS = ["информатики", "физики", "математики", "электроники", "биологии", "химии",
              "экономики", "инженерии", "робототехники", "медиатехнологий", "архитектуры",
              "машиностроения", "телекоммуникаций", "медицины", "экологии", "дизайна"]
SURNAMES = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Волков",
            "Морозов", "Новиков", "Фёдоров", "Соколов", "Михайлов", "Белов", "Орлов",
            "Киселёв", "Макаров", "Захаров", "Никитин", "Егоров", "Гарипов", "Ибрагимов",
            "Смирнова", "Кузнецова", "Петрова", "Волкова", "Морозова", "Соколова"]
FIRST_M = ["Александр", "Сергей", "Дмитрий", "Андрей", "Алексей", "Иван", "Пётр", "Артём",
           "Рустем", "Олег", "Кирилл", "Денис"]
FIRST_F = ["Анна", "Мария", "Елена", "Ольга", "Лейла", "Екатерина", "Татьяна", "Ирина"]
PATR = ["Иванович", "Сергеевич", "Андреевич", "Петрович", "Алексеевич", "Владимирович",
        "Ивановна", "Сергеевна", "Андреевна", "Петровна", "Алексеевна"]
POSITIONS = ["декан", "заведующий кафедрой", "руководитель лаборатории", "директор института",
             "заместитель декана", "начальник учебного центра", "специалист по оборудованию",
             "заведующий лабораторией"]


def fio():
    s = random.choice(SURNAMES)
    if s.endswith("а"):
        return "%s %s %s" % (s, random.choice(FIRST_F), random.choice(PATR))
    return "%s %s %s" % (s, random.choice(FIRST_M), random.choice(PATR))


departments = []
dep_by_un = {}
dep_id = 2001
for (uid, name, short, *_rest) in universities:
    n = random.randint(2, 4)
    topics = random.sample(DEP_TOPICS, n)
    dep_by_un[uid] = []
    for t in topics:
        dname = "%s %s" % (random.choice(DEP_KINDS), t)
        dhead = fio()
        phone = "+7 900 %03d-%02d-%02d" % (random.randint(100, 999), random.randint(10, 99), random.randint(10, 99))
        email = "dep%d@edu.ru" % dep_id
        departments.append((dep_id, uid, dname, dhead, phone, email))
        dep_by_un[uid].append(dep_id)
        dep_id += 1

# ------------------------------------------------------------------------
# 3. Представители вузов
# ------------------------------------------------------------------------

representatives = []
rep_by_un = {}
rep_id = 3001
for (uid, name, short, *_rest) in universities:
    n = random.randint(1, 2)
    rep_by_un[uid] = []
    for _ in range(n):
        dep = random.choice(dep_by_un[uid])
        passport = "%02d%02d%06d" % (random.randint(40, 49), random.randint(10, 25), random.randint(0, 999999))
        phone = "+7 900 %03d-%02d-%02d" % (random.randint(100, 999), random.randint(10, 99), random.randint(10, 99))
        email = "rep%d@edu.ru" % rep_id
        representatives.append((rep_id, uid, dep, fio(), random.choice(POSITIONS),
                                phone, email, passport))
        rep_by_un[uid].append((rep_id, dep))
        rep_id += 1

# ------------------------------------------------------------------------
# 4. Экземпляры техники
# ------------------------------------------------------------------------

# (модель, категория, восстановительная стоимость)
MODELS = [
    (101, 1, 98000), (102, 1, 112000), (103, 1, 175000), (104, 1, 38000), (105, 1, 95000),
    (201, 2, 62000), (202, 2, 89000), (203, 2, 210000), (204, 2, 34000),
    (301, 3, 48000), (302, 3, 72000), (303, 3, 260000), (304, 3, 42000),
    (401, 4, 185000), (402, 4, 52000), (403, 4, 68000), (404, 4, 95000), (405, 4, 720000),
    (501, 5, 65000), (502, 5, 175000), (503, 5, 380000),
    (601, 6, 74000), (602, 6, 24000), (603, 6, 26000),
    (701, 7, 46000), (702, 7, 320000), (703, 7, 290000),
]
MODEL_COST = {m: c for (m, _cat, c) in MODELS}

BRANCHES = ["HQ", "SPB", "KZN", "NSK"]
# сколько экземпляров каждой модели заводится в филиале
QTY_RANGE = {1: (8, 22), 2: (4, 10), 3: (3, 8), 4: (3, 9), 5: (2, 6), 6: (4, 10), 7: (2, 6)}

equipment = []          # (eq_id, inv, mod, br, status, cond, acquire, location, note)
units_by_bm = {}        # (branch, model) -> [eq_id]
unit_branch = {}
eq_id = 100000
for br in BRANCHES:
    for (mod, cat, _cost) in MODELS:
        lo, hi = QTY_RANGE[cat]
        n = random.randint(lo, hi)
        key = (br, mod)
        units_by_bm[key] = []
        for _ in range(n):
            inv = "%s-%08d" % (br, eq_id % 100000000)
            cond = random.choices([1, 2, 3, 4], weights=[15, 45, 30, 10])[0]
            acq = d(-2200, -60)
            loc = "Склад %s-%d" % (br, random.randint(1, 3))
            equipment.append((eq_id, inv, mod, br, "свободна", cond, acq, loc, None))
            units_by_bm[key].append(eq_id)
            unit_branch[eq_id] = br
            eq_id += 1

# ------------------------------------------------------------------------
# 5. Заявки и позиции заявок
# ------------------------------------------------------------------------

def price_per_day(mod):
    # соответствует ROUND(MOD_COST * 0.012, 2) из 02_reference_data.sql
    return round(MODEL_COST[mod] * 0.012 + 1e-9, 2)


STATUS_WEIGHTS = [(2, 20), (3, 15), (4, 8), (5, 15), (6, 35), (7, 7)]
STATUSES = [s for s, w in STATUS_WEIGHTS for _ in range(w)]

requests = []
req_items = []
req_by_un = {}
req_id = 500000
rit_id = 600000
LAPTOPS = [101, 102, 103, 104, 105]

for (uid, name, short, inn, kpp, addr, city, phone, email, br) in universities:
    req_by_un[uid] = []
    for _ in range(random.randint(4, 9)):
        rep, dep = random.choice(rep_by_un[uid])
        status = random.choice(STATUSES)
        if status == 6:                     # выполнена: период полностью в прошлом
            begin = ANCHOR - timedelta(days=random.randint(60, 300))
            end = begin + timedelta(days=random.randint(3, 21))
        elif status == 5:                   # договор: период около текущей даты
            begin = ANCHOR - timedelta(days=random.randint(3, 40))
            end = begin + timedelta(days=random.randint(4, 60))
        else:                               # прочие статусы: период в прошлом
            begin = ANCHOR - timedelta(days=random.randint(30, 300))
            end = begin + timedelta(days=random.randint(3, 21))
        created = begin - timedelta(days=random.randint(3, 25))
        number = "З-%s-%06d" % (br, req_id % 1000000)
        req_id += 1
        items = []
        for mod in random.sample([m for (m, _c, _k) in MODELS], random.randint(1, 3)):
            qty = random.choices([1, 2, 3, 4, 5], weights=[40, 25, 15, 12, 8])[0]
            days = (end - begin).days
            cost = round(price_per_day(mod) * days * qty, 2)
            items.append((rit_id, req_id, mod, qty, begin, end, mod * 10 + 1, cost))
            rit_id += 1
        total = round(sum(i[7] for i in items), 2)
        requests.append((req_id, number, uid, dep, rep, br, created, begin, end, status, total, None))
        req_items.extend(items)
        req_by_un[uid].append((req_id, br, status, items, begin, end, total))
        req_id += 1

# ------------------------------------------------------------------------
# 6. Договоры
# ------------------------------------------------------------------------

contracts = []
contract_by_req = {}
ctr_id = 700000
for (rid, number, uid, dep, rep, br, created, begin, end, status, total, _c) in requests:
    if status not in (5, 6):
        continue
    ctr_id += 1
    cnum = "Д-%s-%06d" % (br, ctr_id % 1000000)
    sign = created + timedelta(days=random.randint(1, 5))
    cbeg = begin
    cend = end
    contracts.append([ctr_id, cnum, rid, sign, cbeg, cend, 0.0, round(total * 0.2, 2),
                      "действует" if status == 5 else "закрыт"])
    contract_by_req[rid] = ctr_id

# ------------------------------------------------------------------------
# 7. Выдачи (по договорам), с учётом занятости экземпляров
# ------------------------------------------------------------------------

# собираем спрос: (begin, end, ctr_id, model, qty, branch)
demands = []
req_lookup = {r[0]: r for r in requests}
for ctr in contracts:
    rid = ctr[2]
    r = req_lookup[rid]
    uid, br = r[2], r[5]
    # позиции заявки
    for it in [x for x in req_items if x[1] == rid]:
        demands.append([it[4], it[5], ctr[0], it[2], it[3], br, rid])

demands.sort(key=lambda x: x[0])

rentals = []
usage = {}          # eq_id -> список интервалов (begin, end)
rnt_id = 800000
emp_by_branch = {"HQ": [2, 4], "SPB": [6, 7], "KZN": [9, 10], "NSK": [11, 12]}
contract_rental_sum = {}


def free_units(branch, model, b, e, need):
    res = []
    for u in units_by_bm[(branch, model)]:
        ok = True
        for (ib, ie) in usage.get(u, []):
            if not (e < ib or b > ie):
                ok = False
                break
        if ok:
            res.append(u)
            if len(res) >= need:
                break
    return res


for (b, e, cid, model, qty, br, rid) in demands:
    chosen = free_units(br, model, b, e, qty)
    if not chosen:
        continue
    days = (e - b).days
    cost = round(price_per_day(model) * days, 2)
    status = req_lookup[rid][9]
    for u in chosen:
        rnt_id += 1
        # выполненные договоры — техника уже возвращена; действующие — часть ещё на руках
        if status == 6:
            ret = e
        else:
            ret = None if random.random() < 0.6 else e
        rentals.append([rnt_id, cid, u, b, e, ret, 3 if random.random() < 0.7 else 2,
                        None, random.choice(emp_by_branch[br]), cost])
        usage.setdefault(u, []).append((b, ret if ret else date(2030, 1, 1)))
        contract_rental_sum[cid] = contract_rental_sum.get(cid, 0.0) + cost

# отбрасываем договоры, по которым не удалось сформировать ни одной выдачи
valid_ctr = set(contract_rental_sum)
contracts = [c for c in contracts if c[0] in valid_ctr]
for c in contracts:
    c[6] = round(contract_rental_sum[c[0]], 2)
    c[7] = round(c[6] * 0.2, 2)
rentals = [r for r in rentals if r[1] in valid_ctr]

# ------------------------------------------------------------------------
# 8. Платежи
# ------------------------------------------------------------------------

payments = []
pay_id = 900000
for c in contracts:
    total = c[6]
    n = random.randint(1, 2)
    if n == 1:
        parts = [total]
    else:
        first = round(total * random.uniform(0.4, 0.6), 2)
        parts = [first, round(total - first, 2)]
    for k, amount in enumerate(parts):
        if amount <= 0:
            continue
        pay_id += 1
        payments.append((pay_id, c[0], c[3] + timedelta(days=k * 10),
                         amount, random.choices([1, 2, 3], weights=[50, 20, 30])[0],
                         "аренда техники", "ПП-%06d" % (pay_id % 1000000)))

# ------------------------------------------------------------------------
# 9. Обслуживание и ремонт
# ------------------------------------------------------------------------

maintenance = []
mnt_id = 950000
for _ in range(260):
    u = random.choice(equipment)[0]
    mb = d(-330, -5)
    mt = random.choices([1, 2, 3, 4, 5], weights=[30, 25, 25, 18, 2])[0]
    me = mb + timedelta(days=random.randint(1, 20))
    cost = 0.0 if mt in (1, 3, 4) else round(random.uniform(1500, 90000), 2)
    mnt_id += 1
    maintenance.append((mnt_id, u, mt, mb, me, cost, "ООО «ТехСервис»",
                        "выполнено" if mt != 5 else "списано"))

# ------------------------------------------------------------------------
# 10. Перемещения техники между филиалами
# ------------------------------------------------------------------------

transfers = []
tr_id = 990000
# перемещаем только свободную технику (не находящуюся сейчас в аренде)
active_now = {r[2] for r in rentals if r[5] is None}
move_pool = random.sample([e[0] for e in equipment if e[0] not in active_now], 40)
for u in move_pool:
    src = unit_branch[u]
    dst = random.choice([b for b in BRANCHES if b != src])
    tr_id += 1
    transfers.append((tr_id, u, src, dst, d(-300, -5),
                      "перераспределение парка по заявкам", "ТН-%06d" % (tr_id % 1000000)))
    unit_branch[u] = dst

# ------------------------------------------------------------------------
# 11. Итоговые статусы экземпляров техники
# ------------------------------------------------------------------------

active_units = {r[2] for r in rentals if r[5] is None}
maintenance_now = {m[1] for m in maintenance if random.random() < 0.15}
written_off = {m[1] for m in maintenance if m[2] == 5}

equipment_final = []
for (eid, inv, mod, _br, _st, cond, acq, loc, note) in equipment:
    br = unit_branch[eid]
    if eid in written_off:
        status = "списана"
    elif eid in active_units:
        status = "аренда"
    elif eid in maintenance_now:
        status = "обслуживание"
    else:
        status = "свободна"
    equipment_final.append((eid, inv, mod, br, status, cond, acq, loc, note))

# ------------------------------------------------------------------------
# 12. Формирование SQL-файла
# ------------------------------------------------------------------------

lines = []
lines.append("-- =====================================================================")
lines.append("--  CampusRent — файл 03: тестовые данные")
lines.append("--  Сгенерировано автоматически: tools/gen_data.py")
lines.append("--  Зерно генератора: 20251009 (данные воспроизводимы)")
lines.append("-- =====================================================================")
lines.append("")
lines.append("USE campusrent;")
lines.append("SET NAMES utf8mb4;")
lines.append("SET FOREIGN_KEY_CHECKS = 0;")
lines.append("")

lines += insert("universities",
                ["UN_ID", "UN_NAME", "UN_SHORT", "UN_INN", "UN_KPP", "UN_ADDRESS",
                 "UN_CITY", "UN_PHONE", "UN_EMAIL", "UN_BR"], universities)
lines.append("")
lines += insert("departments",
                ["DEP_ID", "DEP_UN", "DEP_NAME", "DEP_HEAD", "DEP_PHONE", "DEP_EMAIL"],
                departments)
lines.append("")
lines += insert("representatives",
                ["REP_ID", "REP_UN", "REP_DEP", "REP_FIO", "REP_POSITION",
                 "REP_PHONE", "REP_EMAIL", "REP_PASSPORT"], representatives)
lines.append("")
lines += insert("equipment_units",
                ["EQ_ID", "EQ_INV", "EQ_MOD", "EQ_BR", "EQ_STATUS", "EQ_COND",
                 "EQ_ACQUIRE", "EQ_LOCATION", "EQ_NOTE"], equipment_final)
lines.append("")
lines += insert("requests",
                ["REQ_ID", "REQ_NUMBER", "REQ_UN", "REQ_DEP", "REQ_REP", "REQ_BR",
                 "REQ_CREATED", "REQ_BEGIN", "REQ_END", "REQ_STATUS", "REQ_SUM",
                 "REQ_COMMENT"], requests)
lines.append("")
lines += insert("request_items",
                ["RIT_ID", "RIT_REQ", "RIT_MOD", "RIT_QTY", "RIT_BEGIN", "RIT_END",
                 "RIT_TAR", "RIT_COST"], req_items)
lines.append("")
lines += insert("contracts",
                ["CTR_ID", "CTR_NUMBER", "CTR_REQ", "CTR_SIGN", "CTR_BEGIN",
                 "CTR_END", "CTR_SUM", "CTR_DEPOSIT", "CTR_STATUS"], contracts)
lines.append("")
lines += insert("rentals",
                ["RNT_ID", "RNT_CTR", "RNT_EQ", "RNT_ISSUE", "RNT_DUE", "RNT_RETURN",
                 "RNT_COND_OUT", "RNT_COND_IN", "RNT_EMP", "RNT_COST"], rentals)
lines.append("")
lines += insert("payments",
                ["PAY_ID", "PAY_CTR", "PAY_DATE", "PAY_AMOUNT", "PAY_METHOD",
                 "PAY_PURPOSE", "PAY_DOC"], payments)
lines.append("")
lines += insert("maintenance",
                ["MNT_ID", "MNT_EQ", "MNT_TYPE", "MNT_BEGIN", "MNT_END", "MNT_COST",
                 "MNT_CONTRACTOR", "MNT_RESULT"], maintenance)
lines.append("")
lines += insert("transfers",
                ["TR_ID", "TR_EQ", "TR_FROM", "TR_TO", "TR_DATE", "TR_REASON",
                 "TR_DOC"], transfers)
lines.append("")
lines.append("SET FOREIGN_KEY_CHECKS = 1;")
lines.append("")
lines.append("-- Итоги: %d вузов, %d подразделений, %d представителей," %
             (len(universities), len(departments), len(representatives)))
lines.append("--        %d экземпляров техники, %d заявок, %d позиций," %
             (len(equipment_final), len(requests), len(req_items)))
lines.append("--        %d договоров, %d выдач, %d платежей, %d записей обслуживания, %d перемещений." %
             (len(contracts), len(rentals), len(payments), len(maintenance), len(transfers)))
lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Записано:", OUT)
print("Вузов: %d, подразделений: %d, представителей: %d" %
      (len(universities), len(departments), len(representatives)))
print("Экземпляров: %d, заявок: %d, позиций: %d" %
      (len(equipment_final), len(requests), len(req_items)))
print("Договоров: %d, выдач: %d, платежей: %d, обслуживание: %d, перемещений: %d" %
      (len(contracts), len(rentals), len(payments), len(maintenance), len(transfers)))
