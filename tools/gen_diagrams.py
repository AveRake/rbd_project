#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — генератор схем (SVG) для отчёта.

Создаёт файлы в каталоге diagrams/:
  01_network_scheme.svg      — схема сети
  02_er_diagram.svg          — ER-диаграмма предметной области
  03_db_schema.svg           — схема БД без атрибутов
  04_db_schema_attributes.svg— схема БД с атрибутами
  05_fragmentation.svg       — схема фрагментации
  06_architecture.svg        — архитектура системы
  07_deployment.svg          — диаграмма развёртывания
  08_use_case.svg            — диаграмма вариантов использования

Запуск:  python3 tools/gen_diagrams.py
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "diagrams")

FONT = "Helvetica, Arial, sans-serif"

# Палитра
C_LINE = "#1f2937"
C_REF_F, C_REF_S = "#dbeafe", "#1d4ed8"      # НСИ — синий
C_CLI_F, C_CLI_S = "#dcfce7", "#15803d"      # клиенты — зелёный
C_EQ_F,  C_EQ_S = "#fef9c3", "#a16207"       # техника — жёлтый
C_REQ_F, C_REQ_S = "#fee2e2", "#b91c1c"      # заявки — красный
C_CTR_F, C_CTR_S = "#ffedd5", "#c2410c"      # договоры — оранжевый
C_NEU_F, C_NEU_S = "#f3f4f6", "#4b5563"      # нейтральный
C_HQ_F,  C_HQ_S = "#e0e7ff", "#3730a3"       # ЦО


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    # --- примитивы -----------------------------------------------------
    def rect(self, x, y, w, h, fill="none", stroke=C_LINE, sw=1.5, rx=6, dash=None):
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=14, anchor="middle", weight="normal",
             fill="#111827", italic=False):
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{st}>'
                 f'{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=C_LINE, sw=1.5, dash=None, marker=False):
        d = ' stroke-dasharray="7 5"' if dash else ""
        m = ' marker-end="url(#arrow)"' if marker else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}{m}/>')

    def polygon(self, pts, fill="none", stroke=C_LINE, sw=1.5, dash=None):
        d = ' stroke-dasharray="6 4"' if dash else ""
        p = " ".join(f"{x},{y}" for (x, y) in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}/>')

    def ellipse(self, cx, cy, rx, ry, fill=C_NEU_F, stroke=C_NEU_S):
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="1.5"/>')

    def save(self, name):
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}">'
            f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{C_LINE}"/></marker>'
            f'<marker id="arrowBlue" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{C_REF_S}"/></marker>'
            f'<marker id="arrowRed" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{C_REQ_S}"/></marker>'
            f'</defs>'
            f'<rect width="100%" height="100%" fill="#ffffff"/>'
        )
        body = "\n".join(self.parts)
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(head + body + "\n</svg>\n")

    def header(self, title, subtitle=None):
        self.text(30, 36, title, size=20, anchor="start", weight="bold")
        if subtitle:
            self.text(30, 60, subtitle, size=13, anchor="start", fill="#4b5563")


def center(r):
    x, y, w, h = r
    return (x + w / 2, y + h / 2)


def clip_point(a, b, pad=6):
    """Точка на отрезке a->b, отступив pad от границы прямоугольника a."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    return (ax, ay)


def edge(s, r1, r2, name, c1="1", c2="N", dash=False, off=(0, 0), dcolor=None):
    """Ребро ER: линия + ромб-связь в середине + кардинальности."""
    x1, y1 = center(r1)
    x2, y2 = center(r2)
    mx, my = (x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1]
    col = dcolor or C_LINE
    s.line(x1, y1, mx, my, dash=dash, stroke=col)
    s.line(mx, my, x2, y2, dash=dash, stroke=col)
    # ромб (ширина зависит от длины подписи)
    dw, dh = max(46, len(name) * 4.6), 26
    s.polygon([(mx, my - dh), (mx + dw, my), (mx, my + dh), (mx - dw, my)],
              fill="#ffffff", stroke=col)
    s.text(mx, my + 4, name, size=10.5)
    # кардинальности
    t = 0.24
    s.text(x1 + (mx - x1) * t, y1 + (my - y1) * t, c1, size=12, weight="bold")
    s.text(x2 + (mx - x2) * t, y2 + (my - y2) * t, c2, size=12, weight="bold")


def ent(s, r, ru, en, fill="#ffffff", stroke=C_LINE):
    x, y, w, h = r
    s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=2, rx=4)
    s.text(x + w / 2, y + h / 2 - 2, ru, size=14, weight="bold")
    s.text(x + w / 2, y + h / 2 + 16, en, size=11, fill="#6b7280", italic=True)


# =====================================================================
# 1. СХЕМА СЕТИ
# =====================================================================
def d01_network():
    s = Svg(1200, 720, "Схема сети")
    s.header("Схема сети компании «CampusRent»",
             "Центральный офис и филиалы, обслуживающие вузы регионов")

    hq = (480, 110, 240, 90)
    branches = [(90, 330, 220, 90), (490, 330, 220, 90), (890, 330, 220, 90)]
    blabels = [("Филиал СПб", "Санкт-Петербург"), ("Филиал Казань", "Казань"),
               ("Филиал Новосибирск", "Новосибирск")]

    # соединения ЦО-филиалы
    for b in branches:
        cx1, cy1 = center(hq)
        cx2, cy2 = center(b)
        s.line(cx1, cy1, cx2, cy2, stroke=C_HQ_S, sw=2.5, dash=True)
    s.text(600, 285, "обмен данными (репликация, распределённые запросы)",
           size=12, fill="#374151")

    s.rect(*hq, fill=C_HQ_F, stroke=C_HQ_S, sw=2.5)
    s.text(center(hq)[0], 150, "ЦЕНТРАЛЬНЫЙ ОФИС", size=16, weight="bold")
    s.text(center(hq)[0], 174, "Москва · узел hq", size=12, fill="#374151")

    for b, (t1, t2) in zip(branches, blabels):
        s.rect(*b, fill=C_REF_F, stroke=C_REF_S, sw=2)
        s.text(center(b)[0], b[1] + 40, t1, size=14, weight="bold")
        s.text(center(b)[0], b[1] + 62, t2, size=12, fill="#374151")

    # вузы
    for b in branches:
        bx = center(b)[0]
        for i, dx in enumerate([-70, 0, 70]):
            s.ellipse(bx + dx, 530, 52, 26, fill=C_CLI_F, stroke=C_CLI_S)
            s.text(bx + dx, 534, "ВУЗ", size=12)
        s.line(bx, b[1] + 90, bx, 505, stroke=C_CLI_S)

    s.text(40, 660, "Обозначения: сплошная линия — постоянное подключение; "
                    "пунктир — обмен данными между узлами РБД.", size=12, fill="#4b5563")
    s.text(40, 682, "Каждый филиал хранит локальные данные своего региона "
                    "и реплики центральных справочников.", size=12, fill="#4b5563")
    s.save("01_network_scheme.svg")


# =====================================================================
# 2. ER-ДИАГРАММА
# =====================================================================
def d02_er():
    s = Svg(1620, 1120, "ER-диаграмма")
    s.header("ER-диаграмма предметной области «Сервис аренды техники для вузов»",
             "Ромб — связь; 1 / N — кардинальность; пунктир — необязательная связь")

    R = {
        "categories":  (40, 90, 180, 70),
        "models":      (300, 90, 180, 70),
        "tariffs":     (560, 90, 180, 70),
        "components":  (40, 300, 180, 70),
        "universities": (300, 300, 180, 70),
        "branches":    (1080, 90, 180, 70),
        "employees":   (1340, 90, 180, 70),
        "purposes":    (40, 500, 180, 70),
        "departments": (300, 500, 180, 70),
        "equipment":   (1080, 300, 180, 70),
        "transfers":   (1340, 500, 180, 70),
        "representatives": (40, 700, 180, 70),
        "requests":    (300, 700, 180, 70),
        "items":       (560, 700, 180, 70),
        "rentals":     (1080, 700, 180, 70),
        "maintenance": (1340, 700, 180, 70),
        "contracts":   (560, 920, 180, 70),
        "payments":    (820, 920, 180, 70),
    }
    labels = {
        "categories": ("Категории", "Categories"),
        "models": ("Модели техники", "Models"),
        "tariffs": ("Тарифы", "Tariffs"),
        "components": ("Комплектация", "Model_components"),
        "purposes": ("Назначение", "Model_purposes"),
        "universities": ("ВУЗы (клиенты)", "Universities"),
        "branches": ("Филиалы", "Branches"),
        "employees": ("Сотрудники", "Employees"),
        "departments": ("Подразделения", "Departments"),
        "representatives": ("Представители", "Representatives"),
        "equipment": ("Экземпляры техники", "Equipment_units"),
        "transfers": ("Перемещения", "Transfers"),
        "requests": ("Заявки", "Requests"),
        "items": ("Позиции заявки", "Request_items"),
        "contracts": ("Договоры", "Contracts"),
        "maintenance": ("Обслуживание", "Maintenance"),
        "rentals": ("Выдачи", "Rentals"),
        "payments": ("Платежи", "Payments"),
    }

    edges = [
        ("categories", "models", "относиться", "1", "N", False, (0, 0)),
        ("models", "tariffs", "тарифицироваться", "1", "N", False, (0, 0)),
        ("models", "components", "включать", "1", "N", False, (0, -58)),
        ("models", "purposes", "предназначаться", "1", "N", False, (-60, 95)),
        ("branches", "employees", "работать в", "1", "N", False, (0, 0)),
        ("branches", "equipment", "храниться в", "1", "N", False, (0, 0)),
        ("branches", "universities", "обслуживать", "1", "N", False, (0, 0)),
        ("universities", "departments", "состоять из", "1", "N", False, (0, 0)),
        ("universities", "representatives", "представлять", "1", "N", False, (-40, 40)),
        ("departments", "requests", "относиться", "1", "N", False, (0, 0)),
        ("representatives", "requests", "оформлять", "1", "N", False, (0, 0)),
        ("requests", "items", "содержать", "1", "N", False, (0, 0)),
        ("models", "items", "указываться", "1", "N", False, (0, 0)),
        ("requests", "contracts", "заключаться", "1", "1", True, (0, 0)),
        ("contracts", "rentals", "выдавать", "1", "N", False, (0, 0)),
        ("equipment", "rentals", "использоваться", "1", "N", False, (0, 0)),
        ("equipment", "transfers", "перемещать", "1", "N", False, (70, -60)),
        ("equipment", "maintenance", "обслуживать", "1", "N", True, (0, 90)),
        ("contracts", "payments", "оплачивать", "1", "N", True, (0, 0)),
        ("employees", "rentals", "регистрировать", "1", "N", False, (-40, -40)),
    ]

    for a, b, name, c1, c2, dash, off in edges:
        edge(s, R[a], R[b], name, c1, c2, dash, off)

    fills = {
        "categories": (C_REF_F, C_REF_S), "models": (C_REF_F, C_REF_S),
        "tariffs": (C_REF_F, C_REF_S), "components": (C_REF_F, C_REF_S),
        "purposes": (C_REF_F, C_REF_S),
        "universities": (C_CLI_F, C_CLI_S), "departments": (C_CLI_F, C_CLI_S),
        "representatives": (C_CLI_F, C_CLI_S),
        "equipment": (C_EQ_F, C_EQ_S), "transfers": (C_EQ_F, C_EQ_S),
        "requests": (C_REQ_F, C_REQ_S), "items": (C_REQ_F, C_REQ_S),
        "contracts": (C_CTR_F, C_CTR_S), "rentals": (C_CTR_F, C_CTR_S),
        "payments": (C_CTR_F, C_CTR_S), "maintenance": (C_CTR_F, C_CTR_S),
        "branches": (C_HQ_F, C_HQ_S), "employees": (C_HQ_F, C_HQ_S),
    }
    for k, r in R.items():
        ru, en = labels[k]
        f, st = fills[k]
        ent(s, r, ru, en, fill=f, stroke=st)

    s.text(40, 1050, "Справочные таблицы (статусы заявок, способы оплаты, виды работ, "
                     "степени состояния) на ER-диаграмме не показаны — они введены "
                     "на логическом уровне (см. схему БД).", size=12, fill="#4b5563",
           anchor="start")
    s.save("02_er_diagram.svg")


# =====================================================================
# 3. СХЕМА БД БЕЗ АТРИБУТОВ
# =====================================================================
DB_TABLES = {
    "branches": ("Филиалы", "Branches", C_HQ_F, C_HQ_S),
    "categories": ("Категории", "Categories", C_REF_F, C_REF_S),
    "models": ("Модели", "Models", C_REF_F, C_REF_S),
    "tariffs": ("Тарифы", "Tariffs", C_REF_F, C_REF_S),
    "components": ("Комплектация", "Model_components", C_REF_F, C_REF_S),
    "purposes": ("Назначение", "Model_purposes", C_REF_F, C_REF_S),
    "statuses": ("Статусы заявок", "Request_statuses", C_REF_F, C_REF_S),
    "methods": ("Способы оплаты", "Payment_methods", C_REF_F, C_REF_S),
    "mtypes": ("Виды работ", "Maintenance_types", C_REF_F, C_REF_S),
    "grades": ("Степени состояния", "Condition_grades", C_REF_F, C_REF_S),
    "employees": ("Сотрудники", "Employees", C_HQ_F, C_HQ_S),
    "universities": ("ВУЗы", "Universities", C_CLI_F, C_CLI_S),
    "departments": ("Подразделения", "Departments", C_CLI_F, C_CLI_S),
    "representatives": ("Представители", "Representatives", C_CLI_F, C_CLI_S),
    "equipment": ("Экземпляры техники", "Equipment_units", C_EQ_F, C_EQ_S),
    "transfers": ("Перемещения", "Transfers", C_EQ_F, C_EQ_S),
    "requests": ("Заявки", "Requests", C_REQ_F, C_REQ_S),
    "items": ("Позиции заявки", "Request_items", C_REQ_F, C_REQ_S),
    "contracts": ("Договоры", "Contracts", C_CTR_F, C_CTR_S),
    "rentals": ("Выдачи", "Rentals", C_CTR_F, C_CTR_S),
    "payments": ("Платежи", "Payments", C_CTR_F, C_CTR_S),
    "maintenance": ("Обслуживание", "Maintenance", C_CTR_F, C_CTR_S),
}


def d03_schema():
    s = Svg(1640, 1120, "Схема БД")
    s.header("Схема базы данных «CampusRent» (без атрибутов)",
             "Стрелка — внешний ключ; 1 и N — кардинальность связи; "
             "пунктир — необязательная связь")

    R = {
        "categories":  (40, 100, 200, 74),
        "models":      (300, 100, 200, 74),
        "tariffs":     (560, 100, 200, 74),
        "components":  (40, 320, 200, 74),
        "purposes":    (300, 320, 200, 74),
        "branches":    (860, 100, 200, 74),
        "employees":   (1140, 100, 200, 74),
        "grades":      (1400, 100, 200, 74),
        "universities": (860, 320, 200, 74),
        "departments": (860, 520, 200, 74),
        "representatives": (1140, 520, 200, 74),
        "equipment":   (1140, 320, 200, 74),
        "transfers":   (1400, 320, 200, 74),
        "requests":    (300, 520, 200, 74),
        "items":       (560, 520, 200, 74),
        "statuses":    (40, 520, 200, 74),
        "contracts":   (560, 760, 200, 74),
        "rentals":     (860, 760, 200, 74),
        "payments":    (1140, 760, 200, 74),
        "maintenance": (1400, 760, 200, 74),
        "methods":     (1400, 540, 200, 74),
        "mtypes":      (1400, 920, 200, 74),
    }
    links = [
        ("categories", "models", "1", "N", False),
        ("models", "components", "1", "N", False),
        ("models", "purposes", "1", "N", False),
        ("models", "tariffs", "1", "N", False),
        ("branches", "employees", "1", "N", False),
        ("branches", "universities", "1", "N", False),
        ("branches", "equipment", "1", "N", False),
        ("universities", "departments", "1", "N", False),
        ("universities", "representatives", "1", "N", False),
        ("universities", "requests", "1", "N", False),
        ("departments", "requests", "1", "N", False),
        ("representatives", "requests", "1", "N", False),
        ("statuses", "requests", "1", "N", False),
        ("requests", "items", "1", "N", False),
        ("models", "items", "1", "N", False),
        ("requests", "contracts", "1", "1", True),
        ("contracts", "rentals", "1", "N", False),
        ("equipment", "rentals", "1", "N", False),
        ("equipment", "transfers", "1", "N", False),
        ("equipment", "maintenance", "1", "N", True),
        ("grades", "equipment", "1", "N", False),
        ("contracts", "payments", "1", "N", True),
        ("methods", "payments", "1", "N", False),
        ("mtypes", "maintenance", "1", "N", False),
        ("employees", "rentals", "1", "N", False),
    ]
    for a, b, c1, c2, dash in links:
        x1, y1 = center(R[a])
        x2, y2 = center(R[b])
        s.line(x1, y1, x2, y2, dash=dash, marker=True)
        s.text(x1 + (x2 - x1) * 0.26, y1 + (y2 - y1) * 0.26, c1, size=12, weight="bold")
        s.text(x1 + (x2 - x1) * 0.76, y1 + (y2 - y1) * 0.76, c2, size=12, weight="bold")
    for k, r in R.items():
        ru, en, f, st = DB_TABLES[k]
        ent(s, r, ru, en, fill=f, stroke=st)

    s.text(40, 1060, "Схема совпадает со схемой фрагментации (см. 05_fragmentation). "
                     "Цвет: синий — НСИ, зелёный — клиенты, жёлтый — техника, "
                     "красный — заявки, оранжевый — договоры/финансы.",
           size=12, fill="#4b5563", anchor="start")
    s.save("03_db_schema.svg")


# =====================================================================
# 4. СХЕМА БД С АТРИБУТАМИ
# =====================================================================
ATTR = {
    "branches": ("Филиалы", "Branches", [
        ("BR_ID", "V(8)", "PK"), ("BR_NAME", "V(100)", ""), ("BR_CITY", "V(50)", ""),
        ("BR_ADDRESS", "V(150)", ""), ("BR_PHONE", "V(20)", ""), ("BR_EMAIL", "V(50)", ""),
        ("BR_MANAGER", "V(100)", ""), ("BR_BEGIN", "D", ""), ("BR_END", "D", "")]),
    "categories": ("Категории", "Categories", [
        ("CAT_ID", "N(3)", "PK"), ("CAT_NAME", "V(60)", "U"), ("CAT_DESCR", "V(200)", "")]),
    "models": ("Модели", "Models", [
        ("MOD_ID", "N(6)", "PK"), ("MOD_CAT", "N(3)", "FK"), ("MOD_BRAND", "V(40)", ""),
        ("MOD_NAME", "V(80)", ""), ("MOD_DESCR", "V(300)", ""), ("MOD_COST", "N(12,2)", ""),
        ("MOD_MINQTY", "N(3)", "")]),
    "tariffs": ("Тарифы", "Tariffs", [
        ("TAR_ID", "N(6)", "PK"), ("TAR_MOD", "N(6)", "FK"), ("TAR_UNIT", "V(10)", ""),
        ("TAR_PRICE", "N(10,2)", ""), ("TAR_DEPOSIT", "N(12,2)", ""),
        ("TAR_BEGIN", "D", ""), ("TAR_END", "D", "")]),
    "universities": ("ВУЗы", "Universities", [
        ("UN_ID", "N(6)", "PK"), ("UN_NAME", "V(150)", ""), ("UN_SHORT", "V(60)", "U"),
        ("UN_INN", "C(10)", "U"), ("UN_KPP", "C(9)", ""), ("UN_ADDRESS", "V(150)", ""),
        ("UN_CITY", "V(50)", ""), ("UN_PHONE", "V(20)", ""), ("UN_EMAIL", "V(50)", ""),
        ("UN_BR", "V(8)", "FK")]),
    "employees": ("Сотрудники", "Employees", [
        ("EMP_ID", "N(6)", "PK"), ("EMP_BR", "V(8)", "FK"), ("EMP_FIO", "V(100)", ""),
        ("EMP_POSITION", "V(60)", ""), ("EMP_PHONE", "V(20)", ""),
        ("EMP_EMAIL", "V(50)", ""), ("EMP_LOGIN", "V(30)", "U")]),
    "components": ("Комплектация", "Model_components", [
        ("MC_ID", "BIGINT", "PK"), ("MC_MOD", "N(6)", "FK"), ("MC_ITEM", "V(80)", ""),
        ("MC_QTY", "N(3)", "")]),
    "purposes": ("Назначение", "Model_purposes", [
        ("MP_ID", "BIGINT", "PK"), ("MP_MOD", "N(6)", "FK"), ("MP_PURPOSE", "V(60)", "")]),
    "statuses": ("Статусы заявок", "Request_statuses", [
        ("RST_ID", "N(2)", "PK"), ("RST_NAME", "V(30)", "U")]),
    "methods": ("Способы оплаты", "Payment_methods", [
        ("PM_ID", "N(2)", "PK"), ("PM_NAME", "V(30)", "U")]),
    "mtypes": ("Виды работ", "Maintenance_types", [
        ("MT_ID", "N(2)", "PK"), ("MT_NAME", "V(40)", "U")]),
    "grades": ("Степени состояния", "Condition_grades", [
        ("CG_ID", "N(2)", "PK"), ("CG_NAME", "V(30)", "U")]),
    "departments": ("Подразделения", "Departments", [
        ("DEP_ID", "N(6)", "PK"), ("DEP_UN", "N(6)", "FK"), ("DEP_NAME", "V(100)", ""),
        ("DEP_HEAD", "V(100)", ""), ("DEP_PHONE", "V(20)", ""), ("DEP_EMAIL", "V(50)", "")]),
    "representatives": ("Представители", "Representatives", [
        ("REP_ID", "N(6)", "PK"), ("REP_UN", "N(6)", "FK"), ("REP_DEP", "N(6)", "FK"),
        ("REP_FIO", "V(100)", ""), ("REP_POSITION", "V(60)", ""),
        ("REP_PHONE", "V(20)", ""), ("REP_EMAIL", "V(50)", ""),
        ("REP_PASSPORT", "C(10)", "U")]),
    "equipment": ("Экземпляры техники", "Equipment_units", [
        ("EQ_ID", "N(10)", "PK"), ("EQ_INV", "C(12)", "U"), ("EQ_MOD", "N(6)", "FK"),
        ("EQ_BR", "V(8)", "FK"), ("EQ_STATUS", "V(12)", ""), ("EQ_COND", "N(2)", "FK"),
        ("EQ_ACQUIRE", "D", ""), ("EQ_LOCATION", "V(60)", ""), ("EQ_NOTE", "V(200)", "")]),
    "transfers": ("Перемещения", "Transfers", [
        ("TR_ID", "N(10)", "PK"), ("TR_EQ", "N(10)", "FK"), ("TR_FROM", "V(8)", "FK"),
        ("TR_TO", "V(8)", "FK"), ("TR_DATE", "D", ""), ("TR_REASON", "V(200)", ""),
        ("TR_DOC", "V(30)", "")]),
    "requests": ("Заявки", "Requests", [
        ("REQ_ID", "N(10)", "PK"), ("REQ_NUMBER", "C(12)", "U"), ("REQ_UN", "N(6)", "FK"),
        ("REQ_DEP", "N(6)", "FK"), ("REQ_REP", "N(6)", "FK"), ("REQ_BR", "V(8)", "FK"),
        ("REQ_CREATED", "D", ""), ("REQ_BEGIN", "D", ""), ("REQ_END", "D", ""),
        ("REQ_STATUS", "N(2)", "FK"), ("REQ_SUM", "N(12,2)", ""), ("REQ_COMMENT", "V(300)", "")]),
    "items": ("Позиции заявки", "Request_items", [
        ("RIT_ID", "N(10)", "PK"), ("RIT_REQ", "N(10)", "FK"), ("RIT_MOD", "N(6)", "FK"),
        ("RIT_QTY", "N(3)", ""), ("RIT_BEGIN", "D", ""), ("RIT_END", "D", ""),
        ("RIT_TAR", "N(6)", "FK"), ("RIT_COST", "N(12,2)", "")]),
    "contracts": ("Договоры", "Contracts", [
        ("CTR_ID", "N(10)", "PK"), ("CTR_NUMBER", "C(15)", "U"), ("CTR_REQ", "N(10)", "FK"),
        ("CTR_SIGN", "D", ""), ("CTR_BEGIN", "D", ""), ("CTR_END", "D", ""),
        ("CTR_SUM", "N(12,2)", ""), ("CTR_DEPOSIT", "N(12,2)", ""), ("CTR_STATUS", "V(12)", "")]),
    "rentals": ("Выдачи", "Rentals", [
        ("RNT_ID", "N(10)", "PK"), ("RNT_CTR", "N(10)", "FK"), ("RNT_EQ", "N(10)", "FK"),
        ("RNT_ISSUE", "D", ""), ("RNT_DUE", "D", ""), ("RNT_RETURN", "D", ""),
        ("RNT_COND_OUT", "N(2)", "FK"), ("RNT_COND_IN", "N(2)", "FK"),
        ("RNT_EMP", "N(6)", "FK"), ("RNT_COST", "N(12,2)", "")]),
    "payments": ("Платежи", "Payments", [
        ("PAY_ID", "N(10)", "PK"), ("PAY_CTR", "N(10)", "FK"), ("PAY_DATE", "D", ""),
        ("PAY_AMOUNT", "N(12,2)", ""), ("PAY_METHOD", "N(2)", "FK"),
        ("PAY_PURPOSE", "V(100)", ""), ("PAY_DOC", "V(30)", "")]),
    "maintenance": ("Обслуживание", "Maintenance", [
        ("MNT_ID", "N(10)", "PK"), ("MNT_EQ", "N(10)", "FK"), ("MNT_TYPE", "N(2)", "FK"),
        ("MNT_BEGIN", "D", ""), ("MNT_END", "D", ""), ("MNT_COST", "N(10,2)", ""),
        ("MNT_CONTRACTOR", "V(100)", ""), ("MNT_RESULT", "V(200)", "")]),
}


def d04_schema_attrs():
    cols = 6
    x0, y0 = 40, 110
    cw, gap = 330, 32
    col_x = [x0 + i * (cw + gap) for i in range(cols)]
    order = [
        ["branches", "categories", "models", "tariffs", "universities", "employees"],
        ["components", "purposes", "departments", "representatives", "equipment", "transfers"],
        ["requests", "items", "contracts", "rentals", "payments", "maintenance"],
        ["statuses", "methods", "mtypes", "grades"],
    ]
    row_y = [y0, 520, 840, 1260]
    s = Svg(2320, 1520, "Схема БД с атрибутами")
    s.header("Схема базы данных «CampusRent» с атрибутами",
             "PK — первичный ключ, FK — внешний ключ, U — уникальное поле")

    row_h = 22
    for r_i, row in enumerate(order):
        for c_i, key in enumerate(row):
            ru, en, coldefs = ATTR[key]
            x = col_x[c_i]
            y = row_y[r_i]
            hh = 30 + len(coldefs) * row_h
            s.rect(x, y, cw, hh, fill="#ffffff", stroke=C_LINE, sw=1.5, rx=4)
            s.rect(x, y, cw, 30, fill=C_NEU_F, stroke=C_LINE, sw=1.5, rx=4)
            s.text(x + 12, y + 20, ru, size=14, anchor="start", weight="bold")
            s.text(x + cw - 12, y + 20, en, size=11, anchor="end", fill="#6b7280", italic=True)
            for i, (cname, ctype, flag) in enumerate(coldefs):
                ty = y + 30 + (i + 1) * row_h - 6
                s.text(x + 12, ty, cname, size=12, anchor="start")
                s.text(x + cw - 60, ty, ctype, size=12, anchor="start", fill="#4b5563")
                if flag:
                    s.text(x + cw - 12, ty, flag, size=11, anchor="end",
                           weight="bold", fill="#b91c1c" if flag == "PK" else "#1d4ed8")
            if r_i < len(order) - 1:
                pass
    s.save("04_db_schema_attributes.svg")


# =====================================================================
# 5. СХЕМА ФРАГМЕНТАЦИИ
# =====================================================================
def frag_box(s, x, y, w, h, title, sub, fill, stroke, extra=None):
    s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.8, rx=5)
    s.text(x + w / 2, y + 22, title, size=13, weight="bold")
    if sub:
        s.text(x + w / 2, y + 40, sub, size=10.5, fill="#4b5563", italic=True)
    if extra:
        s.text(x + w / 2, y + h - 10, extra, size=10.5, fill="#374151")


def d05_fragmentation():
    s = Svg(1700, 1030, "Схема фрагментации")
    s.header("Схема фрагментации распределённой БД «CampusRent»",
             "Строки — группы таблиц схемы БД; столбцы — узлы сети; цвет — метод "
             "поддержки распределённости")

    lx, lw = 40, 400
    cols = [("Центральный офис\nhq (Москва)", 460),
            ("Филиал spb\nСанкт-Петербург", 770),
            ("Филиал kzn\nКазань", 1080),
            ("Филиал nsk\nНовосибирск", 1390)]
    cw = 290

    hy = 120
    s.rect(lx, hy, lw, 52, fill=C_NEU_F, stroke=C_NEU_S, sw=1.6, rx=5)
    s.text(lx + lw / 2, hy + 31, "Группа таблиц", size=14, weight="bold")
    for name, x in cols:
        f, st = (C_HQ_F, C_HQ_S) if "Центральный" in name else (C_NEU_F, C_NEU_S)
        s.rect(x, hy, cw, 52, fill=f, stroke=st, sw=1.8, rx=5)
        s.text(x + cw / 2, hy + 24, name.split("\n")[0], size=12.5, weight="bold")
        s.text(x + cw / 2, hy + 41, name.split("\n")[1], size=10.5, fill="#4b5563")

    rows = [
        ("НСИ: справочники (11 таблиц)\nРОК · моментальные снимки", C_REF_F, C_REF_S,
         "основная копия\n(мастер-источник)", "реплика\nполная регенерация 1/сут"),
        ("Клиенты: ВУЗы, подразделения,\nпредставители · РБОК", C_CLI_F, C_CLI_S,
         "реплика\nасинхронное РИ", "реплика\nасинхронное РИ"),
        ("Экземпляры техники\nфрагментация + консолидация", C_EQ_F, C_EQ_S,
         "консолидированная копия\nвсех филиалов", "фрагмент филиала\nEQ_BR = узел"),
        ("Перемещения техники\nфрагментация + консолидация", C_EQ_F, C_EQ_S,
         "консолидированная копия", "локальные записи"),
        ("Заявки и позиции заявки\nРКД + рабочий поток", C_REQ_F, C_REQ_S,
         "консолидация\n+ согласование", "рабочая копия\n(workflow)"),
        ("Договоры и выдачи\nРКД", C_CTR_F, C_CTR_S,
         "консолидированная копия", "локальные данные"),
        ("Платежи\nРКД", C_CTR_F, C_CTR_S,
         "консолидированная копия", "локальные данные"),
        ("Обслуживание и ремонт\nРКД", C_CTR_F, C_CTR_S,
         "консолидированная копия", "локальные данные"),
    ]

    ry = hy + 52
    rh = 84
    for i, (label, f, st, hq_txt, br_txt) in enumerate(rows):
        y = ry + i * (rh + 6)
        # подпись группы
        s.rect(lx, y, lw, rh, fill="#ffffff", stroke=C_NEU_S, sw=1.4, rx=5)
        parts = label.split("\n")
        s.text(lx + lw / 2, y + 32, parts[0], size=12.5, weight="bold")
        s.text(lx + lw / 2, y + 54, parts[1], size=11, fill="#4b5563")
        for j, (name, x) in enumerate(cols):
            txt = hq_txt if j == 0 else br_txt
            s.rect(x, y, cw, rh, fill=f, stroke=st, sw=1.6, rx=5)
            tp = txt.split("\n")
            s.text(x + cw / 2, y + (36 if len(tp) == 1 else 30), tp[0], size=11.5)
            if len(tp) > 1:
                s.text(x + cw / 2, y + 50, tp[1], size=11.5)
        # стрелки направления репликации
        if i == 0:      # РОК: ЦО -> филиалы
            s.line(460 + cw, y + rh / 2, 770, y + rh / 2, stroke=C_REF_S, sw=2.2, marker=True)
            s.line(1080, y + rh / 2, 1390, y + rh / 2, stroke=C_REF_S, sw=2.2, marker=True)
        elif i in (2, 3, 5, 6, 7):   # консолидация: филиалы -> ЦО
            s.line(770, y + rh / 2, 460 + cw, y + rh / 2, stroke=C_CTR_S, sw=2.2, marker=True)

    # Легенда
    ly = ry + len(rows) * (rh + 6) + 16
    s.rect(40, ly, 1620, 120, fill="#ffffff", stroke=C_NEU_S, sw=1.2, rx=6)
    s.text(60, ly + 26, "Легенда:", size=13, weight="bold", anchor="start")
    leg = [(C_REF_F, C_REF_S, "РОК — репликация с основной копией (моментальные снимки)"),
           (C_CLI_F, C_CLI_S, "РБОК — репликация без основной копии (асинхронное РИ)"),
           (C_EQ_F, C_EQ_S, "Фрагментация по филиалам (локальные данные узла)"),
           (C_REQ_F, C_REQ_S, "РКД + рабочий поток (заявки согласуются в ЦО)"),
           (C_CTR_F, C_CTR_S, "РКД — репликация с консолидацией данных")]
    ly2 = ly + 46
    for f, st, t in leg:
        s.rect(64, ly2 - 11, 22, 14, fill=f, stroke=st, sw=1.5, rx=2)
        s.text(96, ly2 + 1, t, size=11.5, anchor="start")
        ly2 += 15
    s.text(900, ly + 26, "Стрелки: → направление передачи данных "
                         "(ЦО → филиал для РОК; филиал → ЦО для консолидации).",
           size=11.5, fill="#4b5563", anchor="start")
    s.save("05_fragmentation.svg")


# =====================================================================
# 6. АРХИТЕКТУРА
# =====================================================================
def d06_architecture():
    s = Svg(1200, 760, "Архитектура")
    s.header("Архитектура распределённой информационной системы",
             "Клиент-серверная архитектура; «тонкий» клиент — браузер")

    # Уровни
    s.rect(60, 110, 1080, 150, fill="#f8fafc", stroke=C_NEU_S, sw=1.2, rx=8, dash=True)
    s.text(80, 136, "Уровень представления (клиенты)", size=14, weight="bold", anchor="start")
    for i, t in enumerate(["Рабочее место\nсотрудника филиала",
                           "Рабочее место\nсотрудника ЦО",
                           "Браузер\nпредставителя ВУЗа"]):
        x = 130 + i * 340
        s.rect(x, 155, 260, 80, fill="#ffffff", stroke=C_NEU_S, sw=1.8, rx=6)
        s.text(x + 130, 190, t.split("\n")[0], size=13, weight="bold")
        s.text(x + 130, 212, t.split("\n")[1], size=12, fill="#4b5563")

    s.rect(60, 300, 1080, 170, fill="#f8fafc", stroke=C_NEU_S, sw=1.2, rx=8, dash=True)
    s.text(80, 326, "Уровень логики приложения (веб-сервер)", size=14, weight="bold", anchor="start")
    for i, t in enumerate(["Модуль работы\nс техникой",
                           "Модуль аренды\n(заявки, договоры)",
                           "Модуль отчётов\nи консолидации"]):
        x = 130 + i * 340
        s.rect(x, 345, 260, 100, fill="#eef2ff", stroke=C_HQ_S, sw=1.8, rx=6)
        s.text(x + 130, 380, t.split("\n")[0], size=13, weight="bold")
        s.text(x + 130, 402, t.split("\n")[1], size=12, fill="#4b5563")

    # СУБД-узлы
    s.rect(60, 510, 1080, 180, fill="#f8fafc", stroke=C_NEU_S, sw=1.2, rx=8, dash=True)
    s.text(80, 536, "Уровень данных (узлы РБД, MySQL)", size=14, weight="bold", anchor="start")
    for i, t in enumerate([("ЦО hq", "мастер НСИ + консолидация"),
                           ("Филиал spb", "сервер БД филиала"),
                           ("Филиал kzn", "сервер БД филиала"),
                           ("Филиал nsk", "сервер БД филиала")]):
        x = 90 + i * 265
        s.rect(x, 555, 245, 110, fill=C_HQ_F if i == 0 else "#fff7ed",
               stroke=C_HQ_S if i == 0 else C_CTR_S, sw=1.8, rx=6)
        s.text(x + 122, 595, t[0], size=14, weight="bold")
        s.text(x + 122, 620, t[1], size=11.5, fill="#4b5563")

    for i in range(3):
        s.line(260 + i * 340, 235, 260 + i * 340, 300, marker=True)
    s.line(600, 470, 600, 510, marker=True)
    s.text(700, 495, "SQL-запросы", size=11.5, fill="#4b5563")
    s.save("06_architecture.svg")


# =====================================================================
# 7. ДИАГРАММА РАЗВЁРТЫВАНИЯ
# =====================================================================
def d07_deployment():
    s = Svg(1300, 820, "Развёртывание")
    s.header("Диаграмма развёртывания (UML)",
             "Взаимодействие узлов РБД через сеть; консолидация — на узле фhq")

    def node(x, y, w, h, title, sub):
        s.rect(x, y, w, h, fill="#ffffff", stroke=C_LINE, sw=1.8, rx=4)
        s.rect(x, y, w, 30, fill=C_NEU_F, stroke=C_LINE, sw=1.5, rx=4)
        s.text(x + w / 2, y + 20, title, size=13, weight="bold")
        s.text(x + w / 2, y + h / 2 + 26, sub, size=11.5, fill="#4b5563")

    node(80, 110, 300, 110, "Web-сервер приложения", "PHP / JavaScript · порт 80")
    node(80, 360, 300, 110, "Рабочие места пользователей", "браузер")

    node(560, 90, 280, 120, "nodes hq (ЦО)", "MySQL 8.0 · порт 3306\nserver-id=1, log-bin")
    node(560, 280, 280, 120, "node spb (филиал)", "MySQL 8.0 · порт 3307\nserver-id=2, slave")
    node(560, 470, 280, 120, "node kzn (филиал)", "MySQL 8.0 · порт 3309\nserver-id=4, slave")
    node(560, 660, 280, 120, "node nsk (филиал)", "MySQL 8.0 · порт 3310\nserver-id=5, slave")
    node(980, 280, 280, 120, "node consol", "MySQL 8.0 · порт 3308\nserver-id=3, consolidation")

    s.line(380, 165, 560, 150, marker=True)
    s.text(470, 145, "TCP/IP", size=11.5, fill="#4b5563")
    s.line(380, 415, 560, 340, marker=True)
    s.text(455, 400, "HTTP", size=11.5, fill="#4b5563")

    for y in (150, 340, 530, 720):
        s.line(840, y, 980, 340, stroke=C_HQ_S, sw=2, dash=True, marker=True)
    s.text(900, 260, "репликация\n(каналы)", size=11, fill=C_HQ_S)
    s.line(700, 210, 700, 280, stroke=C_HQ_S, sw=2, dash=True, marker=True)
    s.text(716, 250, "РОК (НСИ)", size=11, fill=C_HQ_S, anchor="start")
    s.line(720, 370, 720, 470, stroke=C_CLI_S, sw=2, dash=True, marker=True)
    s.text(736, 425, "РБОК (клиенты)", size=11, fill=C_CLI_S, anchor="start")
    s.save("07_deployment.svg")


# =====================================================================
# 8. USE-CASE
# =====================================================================
def d08_usecase():
    s = Svg(1420, 1200, "USE-CASE")
    s.header("Диаграмма вариантов использования (USE-CASE)",
             "Показаны основные роли пользователей и их задачи в системе")

    actors = [
        ("Менеджер филиала", 210),
        ("Сотрудник склада", 370),
        ("Специалист сервиса", 530),
        ("Представитель ВУЗа", 690),
        ("Сотрудник ЦО (номенклатура)", 850),
        ("Бухгалтерия и руководство", 1010),
    ]
    for name, y in actors:
        s.add(f'<circle cx="150" cy="{y-42}" r="19" fill="#ffffff" stroke="{C_LINE}" stroke-width="1.6"/>')
        s.line(150, y - 23, 150, y + 22, sw=1.6)
        s.line(112, y - 2, 188, y - 2, sw=1.6)
        s.line(150, y + 22, 122, y + 62, sw=1.6)
        s.line(150, y + 22, 178, y + 62, sw=1.6)
        s.text(150, y + 86, name, size=12.5, weight="bold")

    usecases = [
        ("Приём и регистрация заявок", 150),
        ("Подбор и бронирование техники", 235),
        ("Оформление договора аренды", 320),
        ("Выдача и возврат техники", 405),
        ("Регистрация платежей", 490),
        ("Учёт экземпляров техники", 575),
        ("Ведение обслуживания и ремонта", 660),
        ("Подача заявки на аренду", 745),
        ("Просмотр своих заявок и договоров", 830),
        ("Ведение номенклатуры и тарифов", 915),
        ("Сводная отчётность по сети", 1000),
        ("Проверка действия репликации", 1085),
    ]
    links = {  # индекс роли -> индексы вариантов использования
        0: [0, 1, 2, 3, 4],
        1: [1, 3, 5],
        2: [5, 6],
        3: [7, 8],
        4: [5, 9],
        5: [4, 10, 11],
    }
    cx, rx = 800, 250
    for ai, uis in links.items():
        ay = actors[ai][1]
        for ui in uis:
            uy = usecases[ui][1]
            s.line(192, ay - 10, cx - rx, uy, stroke="#9aa5b1", sw=1.1)
    for t, y in usecases:
        s.ellipse(cx, y, rx, 34, fill="#eff6ff", stroke=C_HQ_S)
        words = t.split()
        mid = (len(words) + 1) // 2
        if len(t) > 30 and len(words) > 2:
            s.text(cx, y - 2, " ".join(words[:mid]), size=12.5)
            s.text(cx, y + 15, " ".join(words[mid:]), size=12.5)
        else:
            s.text(cx, y + 5, t, size=12.5)
    s.save("08_use_case.svg")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    d01_network()
    d02_er()
    d03_schema()
    d04_schema_attrs()
    d05_fragmentation()
    d06_architecture()
    d07_deployment()
    d08_usecase()
    print("Схемы созданы в", OUT)
