#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — три крупношрифтовые схемы БД с атрибутами (для слайдов).

Создаёт ТОЛЬКО три новых файла в каталоге diagrams/:
  04a_attrs_nsi.svg /.png       — Номенклатура, тарифы и справочники (НСИ)
  04b_attrs_clients.svg /.png   — Клиенты, персонал и техника
  04c_attrs_rental.svg /.png    — Аренда, финансы и сервис

Каждая схема: полотно 1700 x 1150, шрифт полей 22 px, заголовки таблиц 26 px.
Данные берутся из sql/01_schema.sql (источник истины), сверены с
docs/03_Логическое_проектирование.md.

Запуск:
  python3 tools/gen_diagrams_attrs.py            # SVG + PNG (rsvg-convert)
  python3 tools/gen_diagrams_attrs.py --check    # только контроль вёрстки
  python3 tools/gen_diagrams_attrs.py --no-png   # только SVG
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "diagrams")

W, H = 1700, 1150          # полотно
FONT = "Helvetica, Arial, sans-serif"

# --- вёрстка ---------------------------------------------------------------
CW = 780                   # ширина плашки
COL_X = (30, 890)          # левый край колонок (30 + 780 = 810, зазор 80)
Y0 = 98                    # верх первой плашки
ROW_H = 28                 # высота строки поля (шрифт 22)
HEADER_H = 46              # высота шапки таблицы (шрифт 26)
PAD = 6                    # нижний отступ внутри плашки
PAD_X = 20                 # боковой отступ внутри плашки
GAP_MARKS = 10             # зазор между пометками
GAP_COL = 18               # зазор между колонками «имя / тип / пометки»
FS_FIELD = 22              # шрифт полей
FS_HEAD = 26               # шрифт заголовка таблицы
FS_TITLE = 30              # шрифт заголовка схемы
FS_NOTE = 18               # шрифт легенды
FS_FOOT = 17               # шрифт примечаний

# --- палитра (по подсистемам) ---------------------------------------------
SUB = {
    "nsi": ("#dbeafe", "#1d4ed8"),   # НСИ — синий
    "cli": ("#dcfce7", "#15803d"),   # клиенты — зелёный
    "eq":  ("#fef9c3", "#a16207"),   # техника — жёлтый
    "req": ("#fee2e2", "#b91c1c"),   # аренда/заявки — красный
    "ctr": ("#ffedd5", "#c2410c"),   # договоры/финансы/сервис — оранжевый
    "hq":  ("#e0e7ff", "#3730a3"),   # персонал/ЦО — индиго
}
C_LINE = "#1f2937"
C_GRAY = "#4b5563"
C_ROWSEP = "#e5e7eb"

# --- пометки полей ---------------------------------------------------------
MARK_TXT = {"PK": "PK", "FK": "FK", "NN": "NOT NULL", "UQ": "UNIQUE", "CK": "CHECK"}
MARK_COL = {"PK": "#b91c1c", "FK": "#1d4ed8", "NN": "#4b5563",
            "UQ": "#7c3aed", "CK": "#047857"}
MARK_BOLD = {"PK", "FK"}

# --- таблицы (из sql/01_schema.sql) ---------------------------------------
# поле = (имя, тип, пометки, ссылка-вне-строки)
# пометки: PK | FK | NN (NOT NULL) | UQ (UNIQUE по одному полю) | CK (CHECK)
T = {
    # ---------------- 04a: НСИ ----------------
    "models": dict(ru="МОДЕЛИ ТЕХНИКИ", en="models", sub="nsi", f=[
        ("MOD_ID", "N(6)", "PK NN", ""),
        ("MOD_CAT", "N(3)", "FK NN", "categories.CAT_ID"),
        ("MOD_BRAND", "V(40)", "NN", ""),
        ("MOD_NAME", "V(80)", "NN", ""),
        ("MOD_DESCR", "V(300)", "", ""),
        ("MOD_COST", "N(12,2)", "NN CK", ""),
        ("MOD_MINQTY", "N(3)", "NN CK", ""),
    ]),
    "categories": dict(ru="КАТЕГОРИИ ТЕХНИКИ", en="categories", sub="nsi", f=[
        ("CAT_ID", "N(3)", "PK NN", ""),
        ("CAT_NAME", "V(60)", "NN UQ", ""),
        ("CAT_DESCR", "V(200)", "", ""),
    ]),
    "model_components": dict(ru="КОМПЛЕКТАЦИЯ МОДЕЛИ", en="model_components", sub="nsi", f=[
        ("MC_ID", "BIGINT", "PK NN", ""),
        ("MC_MOD", "N(6)", "FK NN", "models.MOD_ID"),
        ("MC_ITEM", "V(80)", "NN", ""),
        ("MC_QTY", "N(3)", "NN CK", ""),
    ]),
    "model_purposes": dict(ru="НАЗНАЧЕНИЕ МОДЕЛИ", en="model_purposes", sub="nsi", f=[
        ("MP_ID", "BIGINT", "PK NN", ""),
        ("MP_MOD", "N(6)", "FK NN", "models.MOD_ID"),
        ("MP_PURPOSE", "V(60)", "NN", ""),
    ]),
    "tariffs": dict(ru="ТАРИФЫ", en="tariffs", sub="nsi", f=[
        ("TAR_ID", "N(6)", "PK NN", ""),
        ("TAR_MOD", "N(6)", "FK NN", "models.MOD_ID"),
        ("TAR_UNIT", "V(10)", "NN CK", ""),
        ("TAR_PRICE", "N(10,2)", "NN CK", ""),
        ("TAR_DEPOSIT", "N(12,2)", "NN CK", ""),
        ("TAR_BEGIN", "DATE", "NN", ""),
        ("TAR_END", "DATE", "CK", ""),
    ]),
    "branches": dict(ru="ФИЛИАЛЫ", en="branches", sub="nsi", f=[
        ("BR_ID", "V(8)", "PK NN", ""),
        ("BR_NAME", "V(100)", "NN", ""),
        ("BR_CITY", "V(50)", "NN", ""),
        ("BR_ADDRESS", "V(150)", "NN", ""),
        ("BR_PHONE", "V(20)", "", ""),
        ("BR_EMAIL", "V(50)", "", ""),
        ("BR_MANAGER", "V(100)", "", ""),
        ("BR_BEGIN", "DATE", "NN", ""),
        ("BR_END", "DATE", "CK", ""),
    ]),
    # ---------------- 04b: клиенты / персонал / техника ----------------
    "employees": dict(ru="СОТРУДНИКИ", en="employees", sub="hq", f=[
        ("EMP_ID", "N(6)", "PK NN", ""),
        ("EMP_BR", "V(8)", "FK NN", "branches.BR_ID"),
        ("EMP_FIO", "V(100)", "NN", ""),
        ("EMP_POSITION", "V(60)", "NN", ""),
        ("EMP_PHONE", "V(20)", "", ""),
        ("EMP_EMAIL", "V(50)", "", ""),
        ("EMP_LOGIN", "V(30)", "NN UQ", ""),
    ]),
    "universities": dict(ru="ВУЗЫ", en="universities", sub="cli", f=[
        ("UN_ID", "N(6)", "PK NN", ""),
        ("UN_NAME", "V(150)", "NN", ""),
        ("UN_SHORT", "V(60)", "NN UQ", ""),
        ("UN_INN", "C(10)", "NN UQ", ""),
        ("UN_KPP", "C(9)", "", ""),
        ("UN_ADDRESS", "V(150)", "NN", ""),
        ("UN_CITY", "V(50)", "NN", ""),
        ("UN_PHONE", "V(20)", "", ""),
        ("UN_EMAIL", "V(50)", "", ""),
        ("UN_BR", "V(8)", "FK NN", "branches.BR_ID"),
    ]),
    "departments": dict(ru="ПОДРАЗДЕЛЕНИЯ ВУЗА", en="departments", sub="cli", f=[
        ("DEP_ID", "N(6)", "PK NN", ""),
        ("DEP_UN", "N(6)", "FK NN", "universities.UN_ID"),
        ("DEP_NAME", "V(100)", "NN", ""),
        ("DEP_HEAD", "V(100)", "", ""),
        ("DEP_PHONE", "V(20)", "", ""),
        ("DEP_EMAIL", "V(50)", "", ""),
    ]),
    "representatives": dict(ru="ПРЕДСТАВИТЕЛИ ВУЗОВ", en="representatives", sub="cli", f=[
        ("REP_ID", "N(6)", "PK NN", ""),
        ("REP_UN", "N(6)", "FK NN", "universities.UN_ID"),
        ("REP_DEP", "N(6)", "FK", "departments.DEP_ID"),
        ("REP_FIO", "V(100)", "NN", ""),
        ("REP_POSITION", "V(60)", "NN", ""),
        ("REP_PHONE", "V(20)", "NN", ""),
        ("REP_EMAIL", "V(50)", "", ""),
        ("REP_PASSPORT", "C(10)", "UQ", ""),
    ]),
    "equipment_units": dict(ru="ЭКЗЕМПЛЯРЫ ТЕХНИКИ", en="equipment_units", sub="eq", f=[
        ("EQ_ID", "N(10)", "PK NN", ""),
        ("EQ_INV", "C(12)", "NN UQ", ""),
        ("EQ_MOD", "N(6)", "FK NN", "models.MOD_ID"),
        ("EQ_BR", "V(8)", "FK NN", "branches.BR_ID"),
        ("EQ_STATUS", "V(12)", "NN CK", ""),
        ("EQ_COND", "N(2)", "FK NN", "condition_grades.CG_ID"),
        ("EQ_ACQUIRE", "DATE", "NN", ""),
        ("EQ_LOCATION", "V(60)", "", ""),
        ("EQ_NOTE", "V(200)", "", ""),
    ]),
    "transfers": dict(ru="ПЕРЕМЕЩЕНИЯ ТЕХНИКИ", en="transfers", sub="eq", f=[
        ("TR_ID", "N(10)", "PK NN", ""),
        ("TR_EQ", "N(10)", "FK NN", "equipment_units.EQ_ID"),
        ("TR_FROM", "V(8)", "FK NN", "branches.BR_ID"),
        ("TR_TO", "V(8)", "FK NN CK", "branches.BR_ID"),
        ("TR_DATE", "DATE", "NN", ""),
        ("TR_REASON", "V(200)", "", ""),
        ("TR_DOC", "V(30)", "", ""),
    ]),
    # ---------------- 04c: аренда / финансы / сервис ----------------
    "requests": dict(ru="ЗАЯВКИ", en="requests", sub="req", f=[
        ("REQ_ID", "N(10)", "PK NN", ""),
        ("REQ_NUMBER", "C(12)", "NN UQ", ""),
        ("REQ_UN", "N(6)", "FK NN", "universities.UN_ID"),
        ("REQ_DEP", "N(6)", "FK NN", "departments.DEP_ID"),
        ("REQ_REP", "N(6)", "FK NN", "representatives.REP_ID"),
        ("REQ_BR", "V(8)", "FK NN", "branches.BR_ID"),
        ("REQ_CREATED", "DATE", "NN", ""),
        ("REQ_BEGIN", "DATE", "NN", ""),
        ("REQ_END", "DATE", "NN CK", ""),
        ("REQ_STATUS", "N(2)", "FK NN", "request_statuses.RST_ID"),
        ("REQ_SUM", "N(12,2)", "NN CK", ""),
        ("REQ_COMMENT", "V(300)", "", ""),
    ]),
    "request_items": dict(ru="ПОЗИЦИИ ЗАЯВКИ", en="request_items", sub="req", f=[
        ("RIT_ID", "N(10)", "PK NN", ""),
        ("RIT_REQ", "N(10)", "FK NN", "requests.REQ_ID"),
        ("RIT_MOD", "N(6)", "FK NN", "models.MOD_ID"),
        ("RIT_QTY", "N(3)", "NN CK", ""),
        ("RIT_BEGIN", "DATE", "NN", ""),
        ("RIT_END", "DATE", "NN CK", ""),
        ("RIT_TAR", "N(6)", "FK NN", "tariffs.TAR_ID"),
        ("RIT_COST", "N(12,2)", "NN CK", ""),
    ]),
    "contracts": dict(ru="ДОГОВОРЫ", en="contracts", sub="ctr", f=[
        ("CTR_ID", "N(10)", "PK NN", ""),
        ("CTR_NUMBER", "C(15)", "NN UQ", ""),
        ("CTR_REQ", "N(10)", "FK NN UQ", "requests.REQ_ID"),
        ("CTR_SIGN", "DATE", "NN", ""),
        ("CTR_BEGIN", "DATE", "NN", ""),
        ("CTR_END", "DATE", "NN CK", ""),
        ("CTR_SUM", "N(12,2)", "NN CK", ""),
        ("CTR_DEPOSIT", "N(12,2)", "NN CK", ""),
        ("CTR_STATUS", "V(12)", "NN CK", ""),
    ]),
    "rentals": dict(ru="ВЫДАЧИ ТЕХНИКИ", en="rentals", sub="ctr", f=[
        ("RNT_ID", "N(10)", "PK NN", ""),
        ("RNT_CTR", "N(10)", "FK NN", "contracts.CTR_ID"),
        ("RNT_EQ", "N(10)", "FK NN", "equipment_units.EQ_ID"),
        ("RNT_ISSUE", "DATE", "NN", ""),
        ("RNT_DUE", "DATE", "NN CK", ""),
        ("RNT_RETURN", "DATE", "CK", ""),
        ("RNT_COND_OUT", "N(2)", "FK NN", "condition_grades.CG_ID"),
        ("RNT_COND_IN", "N(2)", "FK", "condition_grades.CG_ID"),
        ("RNT_EMP", "N(6)", "FK NN", "employees.EMP_ID"),
        ("RNT_COST", "N(12,2)", "NN CK", ""),
    ]),
    "payments": dict(ru="ПЛАТЕЖИ", en="payments", sub="ctr", f=[
        ("PAY_ID", "N(10)", "PK NN", ""),
        ("PAY_CTR", "N(10)", "FK NN", "contracts.CTR_ID"),
        ("PAY_DATE", "DATE", "NN", ""),
        ("PAY_AMOUNT", "N(12,2)", "NN CK", ""),
        ("PAY_METHOD", "N(2)", "FK NN", "payment_methods.PM_ID"),
        ("PAY_PURPOSE", "V(100)", "", ""),
        ("PAY_DOC", "V(30)", "", ""),
    ]),
    "maintenance": dict(ru="ОБСЛУЖИВАНИЕ И РЕМОНТ", en="maintenance", sub="ctr", f=[
        ("MNT_ID", "N(10)", "PK NN", ""),
        ("MNT_EQ", "N(10)", "FK NN", "equipment_units.EQ_ID"),
        ("MNT_TYPE", "N(2)", "FK NN", "maintenance_types.MT_ID"),
        ("MNT_BEGIN", "DATE", "NN", ""),
        ("MNT_END", "DATE", "CK", ""),
        ("MNT_COST", "N(10,2)", "NN CK", ""),
        ("MNT_CONTRACTOR", "V(100)", "", ""),
        ("MNT_RESULT", "V(200)", "", ""),
    ]),
}

LEGEND = ("PK — первичный ключ · FK — внешний ключ · NOT NULL — обязательное · "
          "UNIQUE — уникальное · CHECK — ограничение · «→ таблица.поле» — "
          "внешняя ссылка · N/V/C/D/BIGINT — типы")

# =========================================================================
#  Ширина текста (Helvetica, тысячные доли em) — таблица измерена заранее,
#  внешние библиотеки не требуются.
# =========================================================================
W1000 = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556,
    "@": 1015, "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778,
    "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
    "`": 333, "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556,
    "h": 556, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556,
    "p": 556, "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722,
    "x": 500, "y": 500, "z": 500, "{": 334, "|": 260, "}": 334, "~": 584,
    "А": 678, "Б": 662, "В": 667, "Г": 519, "Д": 701, "Е": 667, "Ж": 992, "З": 666,
    "И": 722, "Й": 722, "К": 667, "Л": 687, "М": 833, "Н": 722, "О": 778, "П": 722,
    "Р": 667, "С": 722, "Т": 611, "У": 667, "Ф": 855, "Х": 667, "Ц": 732, "Ч": 651,
    "Ш": 944, "Щ": 954, "Ъ": 833, "Ы": 879, "Ь": 651, "Э": 722, "Ю": 1000, "Я": 714,
    "а": 556, "б": 556, "в": 548, "г": 403, "д": 606, "е": 556, "ж": 780, "з": 500,
    "и": 584, "й": 584, "к": 548, "л": 574, "м": 666, "н": 556, "о": 556, "п": 556,
    "р": 556, "с": 500, "т": 500, "у": 500, "ф": 832, "х": 500, "ц": 571, "ч": 538,
    "ш": 778, "щ": 792, "ъ": 611, "ы": 722, "ь": 500, "э": 510, "ю": 778, "я": 558,
    "→": 634, "·": 278, "№": 901, "«": 556, "»": 556, "—": 1000, "–": 556,
}
BOLD_K = 1.06          # жирный шрифт шире примерно на 6 %


def tw(s, size, bold=False):
    """Ширина строки в px."""
    w = sum(W1000.get(ch, 556) for ch in s) * size / 1000.0
    return w * (BOLD_K if bold else 1.0)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# =========================================================================
#  SVG
# =========================================================================
class Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=C_LINE, sw=1.5, rx=8, dash=None):
        d = ' stroke-dasharray="7 5"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=C_LINE, sw=1.5, dash=None):
        d = ' stroke-dasharray="7 5"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def poly(self, pts, stroke=C_LINE, sw=2.4):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polyline points="{p}" fill="none" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="round" '
                 f'stroke-linejoin="round"/>')

    def text(self, x, y, s, size=22, anchor="start", weight="normal", fill="#111827",
             italic=False, halo=False):
        st = ' font-style="italic"' if italic else ""
        hl = (' stroke="#ffffff" stroke-width="5" paint-order="stroke" '
              'stroke-linejoin="round"') if halo else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" '
                 f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
                 f'fill="{fill}"{st}{hl}>{esc(s)}</text>')

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="#ffffff"/>')
        body = "\n".join(self.parts)
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n" + body + "\n</svg>\n")
        return path


# =========================================================================
#  Плашки и связи
# =========================================================================
def card_h(key):
    return HEADER_H + len(T[key]["f"]) * ROW_H + PAD


def marks_str(marks):
    return " ".join(MARK_TXT[m] for m in marks.split())


def marks_w(marks):
    if not marks:
        return 0.0
    parts = marks.split()
    return sum(tw(MARK_TXT[m], FS_FIELD, m in MARK_BOLD) for m in parts) \
        + GAP_MARKS * (len(parts) - 1)


def row_metrics(key):
    """Ширины колонок «имя» и «тип» (выравнивание внутри плашки)."""
    fs = T[key]["f"]
    return (max(tw(f[0], FS_FIELD) for f in fs),
            max(tw(f[1], FS_FIELD) for f in fs))


def draw_card(s, key, x, y):
    t = T[key]
    fs = t["f"]
    fill, stroke = SUB[t["sub"]]
    h = card_h(key)

    # корпус
    s.rect(x, y, CW, h, fill="#ffffff", stroke=stroke, sw=2, rx=9)
    # шапка (пастель)
    s.rect(x, y, CW, HEADER_H, fill=fill, stroke="none", sw=0, rx=9)
    s.rect(x, y + HEADER_H - 12, CW, 12, fill=fill, stroke="none", sw=0, rx=0)
    s.line(x, y + HEADER_H, x + CW, y + HEADER_H, stroke=stroke, sw=2)
    # контур поверх
    s.rect(x, y, CW, h, fill="none", stroke=stroke, sw=2, rx=9)

    # шапка: русское название + латинское имя
    s.text(x + PAD_X, y + 32, t["ru"], size=FS_HEAD, weight="bold", fill=stroke)
    s.text(x + CW - PAD_X, y + 32, f"({t['en']})", size=FS_FIELD, anchor="end",
           italic=True, fill=C_GRAY)

    name_w, type_w = row_metrics(key)
    name_x = x + PAD_X
    type_x_al = name_x + name_w + GAP_COL
    marks_x_al = type_x_al + type_w + GAP_COL
    target_right = x + CW - PAD_X

    for i, (nm, tp, mk, ref) in enumerate(fs):
        top = y + HEADER_H + i * ROW_H
        base = top + ROW_H - 8
        if i:
            s.line(x + 10, top, x + CW - 10, top, stroke=C_ROWSEP, sw=1)
        # колонки «имя / тип» выровнены; если длинная внешняя ссылка
        # не оставляет места пометкам, тип и пометки строки сдвигаются влево
        mw = marks_w(mk)
        ref_w = tw("→ " + ref, FS_FIELD) if ref else 0.0
        limit = x + CW - PAD_X - (ref_w + 16 if ref else 0.0)
        type_x, type_col_w = type_x_al, type_w
        if marks_x_al + mw > limit:
            type_x = max(name_x + tw(nm, FS_FIELD) + GAP_COL,
                         type_x_al - (marks_x_al + mw - limit))
            type_col_w = tw(tp, FS_FIELD)
        marks_x = type_x + type_col_w + GAP_COL
        s.text(name_x, base, nm, size=FS_FIELD)
        s.text(type_x, base, tp, size=FS_FIELD, fill=C_GRAY)
        mx = marks_x
        for m in mk.split():
            s.text(mx, base, MARK_TXT[m], size=FS_FIELD,
                   weight="bold" if m in MARK_BOLD else "normal", fill=MARK_COL[m])
            mx += tw(MARK_TXT[m], FS_FIELD, m in MARK_BOLD) + GAP_MARKS
        if ref:
            s.text(target_right, base, "→ " + ref, size=FS_FIELD, anchor="end",
                   italic=True, fill=C_GRAY)


def link_lines(s, L):
    s.poly(L["pts"], stroke=C_LINE, sw=2.4)


def link_labels(s, L):
    if L.get("l1"):
        s.text(L["l1"][0], L["l1"][1], "1", size=FS_FIELD, weight="bold",
               anchor="middle", fill=C_LINE, halo=True)
    if L.get("l2"):
        s.text(L["l2"][0], L["l2"][1], "N", size=FS_FIELD, weight="bold",
               anchor="middle", fill=C_LINE, halo=True)
    if L.get("mid"):
        mx, my = L["mid"]
        s.rect(mx - 35, my - 17, 70, 28, fill="#ffffff", stroke="#9ca3af",
               sw=1.3, rx=6)
        s.text(mx, my + 3, "1 : N", size=FS_FIELD, anchor="middle", fill=C_LINE)


def render(s, pos, links, notes):
    """Сначала линии, затем плашки (перекрывают линии), затем подписи."""
    for L in links:
        link_lines(s, L)
    for k, (x, y) in pos.items():
        draw_card(s, k, x, y)
    for L in links:
        link_labels(s, L)
    note_lines(s, notes)


def note_lines(s, notes):
    y = H - 40
    for n in reversed(notes):
        s.text(30, y, n, size=FS_FOOT, fill=C_GRAY)
        y -= 25


# =========================================================================
#  Схема 04a — Номенклатура, тарифы и справочники
# =========================================================================
def d04a(check=False):
    s = Svg(W, H)
    s.text(30, 44, "Схема БД «CampusRent» с атрибутами — "
                   "Номенклатура, тарифы и справочники (НСИ)",
           size=FS_TITLE, weight="bold")
    s.text(30, 76, LEGEND, size=FS_NOTE, fill=C_GRAY)

    x0, x1 = COL_X
    G = 130
    pos = {}
    # раскладка колонки 1
    y = Y0
    for k in ("models", "model_components", "model_purposes"):
        pos[k] = (x0, y)
        y += card_h(k) + G
    # раскладка колонки 2 (tariffs выровнен с models)
    y = Y0
    for k in ("tariffs", "categories", "branches"):
        pos[k] = (x1, y)
        y += card_h(k) + G

    def R(k):
        x, yy = pos[k]
        return dict(x=x, y=yy, w=CW, h=card_h(k),
                    r=x + CW, b=yy + card_h(k), c=yy + card_h(k) / 2)

    m, t, c, mc, mp = R("models"), R("tariffs"), R("categories"), \
        R("model_components"), R("model_purposes")

    links = [
        # categories → models
        dict(pts=[(c["x"] + 26, c["c"]), (850, c["c"]), (850, 300), (m["r"] - 26, 300)],
             l1=(828, 266), l2=(872, c["c"] - 14), mid=(850, (c["c"] + 300) / 2)),
        # models → tariffs
        dict(pts=[(m["r"] - 26, m["c"]), (t["x"] + 26, t["c"])],
             l1=(826, m["c"] - 12), l2=(874, t["c"] - 12)),
        # models → model_components
        dict(pts=[(420, m["b"] - 26), (420, mc["y"] + 26)],
             l1=(398, m["b"] + 26), l2=(444, mc["y"] - 8),
             mid=(478, (m["b"] + mc["y"]) / 2)),
        # models → model_purposes
        dict(pts=[(m["r"] - 26, 320), (830, 320), (830, mp["c"]), (m["r"] - 26, mp["c"])],
             l1=(852, 312), l2=(856, mp["c"] - 10), mid=(850, 650)),
    ]
    render(s, pos, links, [
        "Составные ключи UNIQUE: models(MOD_BRAND, MOD_NAME) · "
        "model_components(MC_MOD, MC_ITEM) · model_purposes(MP_MOD, MP_PURPOSE) · "
        "tariffs(TAR_MOD, TAR_UNIT, TAR_BEGIN)",
        "branches — родительское отношение для employees, universities, "
        "equipment_units, transfers, requests (см. схемы 04b и 04c)",
    ])
    return s, pos


# =========================================================================
#  Схема 04b — Клиенты, персонал и техника
# =========================================================================
def d04b(check=False):
    s = Svg(W, H)
    s.text(30, 44, "Схема БД «CampusRent» с атрибутами — "
                   "Клиенты, персонал и техника",
           size=FS_TITLE, weight="bold")
    s.text(30, 76, LEGEND, size=FS_NOTE, fill=C_GRAY)

    x0, x1 = COL_X
    G = 40
    pos = {}
    y = Y0
    for k in ("universities", "representatives", "employees"):
        pos[k] = (x0, y)
        y += card_h(k) + G
    y = Y0
    for k in ("departments", "equipment_units", "transfers"):
        pos[k] = (x1, y)
        y += card_h(k) + G

    def R(k):
        x, yy = pos[k]
        return dict(x=x, y=yy, w=CW, h=card_h(k),
                    r=x + CW, b=yy + card_h(k))

    un, dp, rp, eq, tr = R("universities"), R("departments"), \
        R("representatives"), R("equipment_units"), R("transfers")

    links = [
        # universities → departments
        dict(pts=[(un["r"] - 26, 180), (dp["x"] + 26, 180)],
             l1=(826, 168), l2=(874, 168)),
        # departments → representatives
        dict(pts=[(dp["x"] + 26, 280), (850, 280), (850, 615), (rp["r"] - 26, 615)],
             l1=(874, 268), l2=(836, 604), mid=(850, 448)),
        # universities → representatives
        dict(pts=[(420, un["b"] - 26), (420, rp["y"] + 26)],
             l1=(398, un["b"] + 26), l2=(444, rp["y"] - 8)),
        # equipment_units → transfers
        dict(pts=[(1280, eq["b"] - 26), (1280, tr["y"] + 26)],
             l1=(1258, eq["b"] + 26), l2=(1304, tr["y"] - 8)),
    ]
    render(s, pos, links, [
        "Составной ключ UNIQUE: departments(DEP_UN, DEP_NAME) · CHECK: "
        "transfers(TR_FROM <> TR_TO), equipment_units(EQ_STATUS — допустимые статусы)",
        "Ссылки за пределы схемы: branches (BR_ID), models (MOD_ID), "
        "condition_grades (CG_ID) — см. схемы 04a и 04c",
    ])
    return s, pos


# =========================================================================
#  Схема 04c — Аренда, финансы и сервис
# =========================================================================
def d04c(check=False):
    s = Svg(W, H)
    s.text(30, 44, "Схема БД «CampusRent» с атрибутами — "
                   "Аренда, финансы и сервис",
           size=FS_TITLE, weight="bold")
    s.text(30, 76, LEGEND, size=FS_NOTE, fill=C_GRAY)

    x0, x1 = COL_X
    G = 26
    pos = {}
    y = Y0
    for k in ("requests", "maintenance", "payments"):
        pos[k] = (x0, y)
        y += card_h(k) + G
    y = Y0
    for k in ("request_items", "contracts", "rentals"):
        pos[k] = (x1, y)
        y += card_h(k) + G

    def R(k):
        x, yy = pos[k]
        return dict(x=x, y=yy, w=CW, h=card_h(k),
                    r=x + CW, b=yy + card_h(k))

    rq, ri, ct, rn = R("requests"), R("request_items"), R("contracts"), R("rentals")

    links = [
        # requests → request_items
        dict(pts=[(rq["r"] - 26, 180), (ri["x"] + 26, 180)],
             l1=(826, 168), l2=(874, 168)),
        # requests → contracts
        dict(pts=[(rq["r"] - 26, 460), (850, 460), (850, 560), (ct["x"] + 26, 560)],
             l1=(840, 448), l2=(874, 548), mid=(850, 510)),
        # contracts → rentals
        dict(pts=[(1280, ct["b"] - 26), (1280, rn["y"] + 26)],
             l1=(1258, ct["b"] + 22), l2=(1304, rn["y"] - 6)),
        # contracts → payments
        dict(pts=[(ct["x"] + 26, 690), (850, 690), (850, 940),
                  (rq["x"] + CW - 26, 940)],
             l1=(826, 678), l2=(842, 928), mid=(850, 790)),
    ]
    render(s, pos, links, [
        "Составные ключи UNIQUE: request_items(RIT_REQ, RIT_MOD, RIT_BEGIN) · "
        "rentals(RNT_EQ, RNT_ISSUE)",
        "Справочные таблицы request_statuses, payment_methods, maintenance_types, "
        "condition_grades на схеме не показаны (см. 04_db_schema_attributes)",
    ])
    return s, pos


# =========================================================================
#  Контроль вёрстки
# =========================================================================
def check_layout():
    ok = True
    print("=" * 78)
    for key, t in T.items():
        name_w, type_w = row_metrics(key)
        name_x, type_x = PAD_X, PAD_X + name_w + GAP_COL
        marks_x = type_x + type_w + GAP_COL
        worst = 0.0
        for nm, tp, mk, ref in t["f"]:
            mx = min(marks_x, PAD_X + tw(nm, FS_FIELD) + GAP_COL
                     + tw(tp, FS_FIELD) + GAP_COL)
            end = mx + marks_w(mk)
            total = end
            if ref:
                tw_ref = tw("→ " + ref, FS_FIELD)
                start = CW - PAD_X - tw_ref
                total = max(end, CW - PAD_X)
                if start < end + 12:
                    ok = False
                    print(f"  !! {key}.{nm}: пометки пересекают ссылку "
                          f"({start:.0f} < {end:.0f} + 12)")
            worst = max(worst, total)
        head = tw(t["ru"], FS_HEAD, bold=True) + tw(f"({t['en']})", FS_FIELD) + 24 + 2 * PAD_X
        if head > CW:
            ok = False
            print(f"  !! {key}: шапка {head:.0f} > {CW}")
        print(f"  {key:<18} полей {len(t['f']):>2}  строк  {worst:>6.1f} px  "
              f"шапка {head:>6.1f} px  (плашка {CW})")
    print("-" * 78)
    print(f"  легенда: {tw(LEGEND, FS_NOTE):.0f} px (полотно {W})")
    if tw(LEGEND, FS_NOTE) > W - 60:
        ok = False
        print("  !! легенда не помещается в одну строку")
    for name, fn in (("04a", d04a), ("04b", d04b), ("04c", d04c)):
        s, pos = fn(check=True)
        bottom = max(y + card_h(k) for k, (x, y) in pos.items())
        print(f"  {name}: низа плашек — {bottom:.0f} px (полотно {H})")
        if bottom > H - 82:
            ok = False
            print(f"  !! {name}: плашки заходят на строку примечаний")
        for k, (x, y) in pos.items():
            if x + CW > W - 20:
                ok = False
                print(f"  !! {name}: {k} выходит за полотно")
    print("=" * 78)
    print("вёрстка: " + ("OK" if ok else "есть замечания"))
    return ok


def main():
    args = sys.argv[1:]
    check_layout()
    if "--check" in args:
        return
    for name, fn in (("04a_attrs_nsi", d04a), ("04b_attrs_clients", d04b),
                     ("04c_attrs_rental", d04c)):
        s, _ = fn()
        svg = s.save(name + ".svg")
        print("SVG:", svg)
        if "--no-png" not in args:
            png = os.path.join(OUT, name + ".png")
            subprocess.run(["rsvg-convert", "-w", str(W), svg, "-o", png],
                           check=True)
            print("PNG:", png)


if __name__ == "__main__":
    main()
