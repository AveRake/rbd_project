#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — переработанная (читаемая) диаграмма вариантов использования.

Создаёт:
    diagrams/08b_use_case.svg
    diagrams/08b_use_case.png      (rsvg-convert -w 1700 ...)

Ключевые решения по компоновке
------------------------------
* Полотно 1700x950 — горизонтальное, хорошо ложится на слайд 16:9
  (на слайде шириной ~1100 px уменьшение всего в 1.55 раза).
* Актёры — одним столбцом слева, крупные фигурки «человечек».
* Варианты использования — двумя колонками по 6 штук справа.
* Все подписи >= 26 px, заголовок — 30 px.
* Линии связи — ортогональные (манхэттенские) и разведены по свободным
  коридорам:
      - вертикальные «шины» актёров лежат в коридоре между подписями
        актёров и левой колонкой овалов;
      - в левую колонку линия входит горизонтально в левую вершину овала;
      - в правую колонку линия уходит по горизонтальной «полке» строго
        в зазоре между строками левой колонки, затем по вертикальному
        каналу между колонками и входит в левую вершину овала правой
        колонки.
  За счёт этого ни одна линия не проходит сквозь овалы, сквозь текст
  вариантов использования и сквозь подписи актёров.

Источник ролей и прецедентов: docs/01_ТЗ_постановка_задачи.md,
разделы 1.4 «Роли пользователей и их задачи» и 1.5 «Функциональные
требования» (подсистемы 1.5.1–1.5.6).

Запуск:  python3 tools/gen_usecase_v2.py
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "diagrams")
SVG_NAME = "08b_use_case.svg"
PNG_NAME = "08b_use_case.png"

FONT = "Helvetica, Arial, sans-serif"

# --------------------------------------------------------------------------
# палитра (по требованию к оформлению)
# --------------------------------------------------------------------------
C_BG = "#ffffff"
C_TITLE = "#102D69"
C_ACTOR = "#000000"          # актёры — чёрные линии
C_ACTOR_LBL = "#102D69"      # подписи актёров — тёмно-синие
C_UC_TEXT = "#102D69"
C_UC_FILL = "#eff6ff"        # светлая заливка овалов
C_UC_STROKE = "#1d4ed8"      # синяя обводка овалов
C_LINK = "#475569"           # линии связи

# --------------------------------------------------------------------------
# геометрия полотна
# --------------------------------------------------------------------------
W, H = 1700, 950
TITLE = "Диаграмма вариантов использования (USE-CASE)"
TITLE_SIZE = 30
FS_ACTOR = 26               # подписи актёров
FS_UC = 26                  # текст внутри овалов
MIN_FONT = 26

# актёры: фигурки в один столбец слева
AX = 195                    # центр фигурки по X
AY0, AY_STEP = 131, 124     # центр фигурки по Y (7 актёров)
HEAD_R = 15
ARM_HALF = 34
LEG_HALF = 24
SPINE_X0 = AX + ARM_HALF    # начало горизонтальной «шины» актёра (229)

ACTORS = [
    "Менеджер филиала",
    "Сотрудник склада",
    "Специалист сервиса",
    "Руководитель филиала",
    "Представитель вуза",
    "Сотрудник ЦО",
    "Руководство и бухгалтерия",
]
AY = [AY0 + i * AY_STEP for i in range(len(ACTORS))]

# варианты использования: две колонки по 6
ROW_Y = [135 + i * 151 for i in range(6)]
COL1_CX, COL2_CX = 820, 1400
RX, RY = 260, 48            # овал 520 x 96
COL1_LEFT = COL1_CX - RX    # 560  — левая вершина овала 1-й колонки
COL2_LEFT = COL2_CX - RX    # 1140 — левая вершина овала 2-й колонки

# id варианта использования -> (подпись, колонка, строка)
UC = {
    1:  ("Приём и регистрация заявок",          1, 0),
    2:  ("Подбор и бронирование техники",       1, 1),
    3:  ("Оформление договоров аренды",         1, 2),
    4:  ("Выдача и возврат техники",            1, 3),
    5:  ("Регистрация платежей",                1, 4),
    6:  ("Учёт экземпляров техники",            1, 5),
    7:  ("Учёт состояния техники",              2, 0),
    8:  ("Ведение обслуживания и ремонта",      2, 1),
    9:  ("Подача заявки вузом",                 2, 2),
    10: ("Просмотр своих заявок и договоров",   2, 3),
    11: ("Ведение номенклатуры и тарифов",      2, 4),
    12: ("Сводные отчёты по сети",              2, 5),
}

# актёр (индекс) -> варианты использования
LINKS = {
    0: [1, 2, 3, 4, 5],      # Менеджер филиала
    1: [2, 4, 6, 7],         # Сотрудник склада
    2: [7, 8],               # Специалист сервиса
    3: [1, 12],              # Руководитель филиала
    4: [9, 10],              # Представитель вуза
    5: [6, 11],              # Сотрудник ЦО
    6: [3, 5, 12],           # Руководство и бухгалтерия
}

# вертикальные «шины» актёров (x) — правее подписей актёров
TRUNK_X = [395 + 25 * i for i in range(len(ACTORS))]

# горизонтальные «полки» для перехода в правую колонку.
# Значения подобраны строго в зазорах между строками левой колонки:
#   зазоры: 183-238, 334-389, 485-540, 636-691, 787-842
COL2_LANE = {
    (1, 7): 196,     # Сотрудник склада  -> Учёт состояния техники
    (2, 7): 218,     # Специалист сервиса-> Учёт состояния техники
    (2, 8): 350,     # Специалист сервиса-> Ведение обслуживания и ремонта
    (4, 9): 500,     # Представитель вуза-> Подача заявки вузом
    (3, 12): 650,    # Руководитель филиала -> Сводные отчёты по сети
    (4, 10): 672,    # Представитель вуза-> Просмотр своих заявок и договоров
    (5, 11): 800,    # Сотрудник ЦО      -> Ведение номенклатуры и тарифов
    (6, 12): 822,    # Руководство и бухгалтерия -> Сводные отчёты по сети
}
# вертикальный канал между колонками овалов (1080..1140) — по каналу на линию
COL2_CH_X = {
    (1, 7): 1085, (2, 7): 1090, (2, 8): 1095, (4, 9): 1100,
    (3, 12): 1105, (4, 10): 1110, (5, 11): 1115, (6, 12): 1120,
}
# Если к варианту использования ведут линии нескольких актёров, они входят
# в овал в РАЗНЫХ точках левой дуги — иначе линии слились бы в одну и было
# бы не видно, что актёров несколько.
ENTRY_DY = {1: [0], 2: [-20, 20], 3: [-26, 0, 26]}


def uc_entries():
    """u -> {индекс актёра: смещение точки входа по Y от центра овала}."""
    res = {}
    for u in UC:
        conns = sorted(ai for ai, ucs in LINKS.items() if u in ucs)
        dys = ENTRY_DY.get(len(conns))
        if dys is None:                       # запасной вариант: равномерно
            step = 52.0 / max(1, len(conns) - 1)
            dys = [-26 + step * k for k in range(len(conns))]
        res[u] = dict(zip(conns, dys))
    return res


ENTRIES = uc_entries()


def entry_point(ai, u):
    """Точка на левой дуге овала, в которую входит линия актёра ai."""
    dy = ENTRIES[u][ai]
    _, col, row = UC[u]
    cx = COL1_CX if col == 1 else COL2_CX
    cy = ROW_Y[row] + dy
    dx = RX * (1 - (dy / RY) ** 2) ** 0.5
    return (cx - dx, cy)


# ==========================================================================
# мини-библиотека SVG (чистый Python, без внешних зависимостей)
# ==========================================================================
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts = []

    def raw(self, s):
        self.parts.append(s)

    def line(self, x1, y1, x2, y2, stroke=C_LINK, sw=1.8, cap="round"):
        self.raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="{cap}"/>')

    def polyline(self, pts, stroke=C_LINK, sw=1.8):
        p = " ".join(f"{x},{y}" for (x, y) in pts)
        self.raw(f'<polyline points="{p}" fill="none" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

    def ellipse(self, cx, cy, rx, ry, fill=C_UC_FILL, stroke=C_UC_STROKE, sw=2.4):
        self.raw(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, cx, cy, r, fill="#ffffff", stroke=C_ACTOR, sw=2.0):
        self.raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=FS_UC, anchor="middle", weight="normal",
             fill=C_UC_TEXT):
        self.raw(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">'
                 f'{esc(s)}</text>')

    def save(self, path):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="{C_BG}"/>')
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n" + "\n".join(self.parts) + "\n</svg>\n")


# ==========================================================================
# вспомогательное: приблизительная ширина текста (для самопроверки)
# ==========================================================================
# Ширины символов Arial в долях em (для точной оценки ширины текста).
_W_REG = {
   " ": 0.278, "(": 0.333, ")": 0.333, ",": 0.278, "-": 0.333, ".": 0.278, "/": 0.278,
   "0": 0.556, ":": 0.278, "A": 0.667, "C": 0.722, "E": 0.667, "G": 0.778, "H": 0.722,
   "N": 0.722, "O": 0.778, "P": 0.667, "R": 0.722, "S": 0.667, "T": 0.611, "U": 0.722,
   "[": 0.278, "]": 0.278, "a": 0.556, "b": 0.556, "c": 0.500, "d": 0.556, "e": 0.556,
   "f": 0.278, "g": 0.556, "i": 0.222, "l": 0.222, "m": 0.833, "n": 0.556, "o": 0.556,
   "p": 0.556, "r": 0.333, "s": 0.500, "t": 0.278, "u": 0.556, "v": 0.500, "w": 0.722,
   "x": 0.500, "{": 0.334, "}": 0.334, "«": 0.556, "»": 0.556, "А": 0.667, "В": 0.667,
   "Г": 0.542, "Д": 0.677, "Е": 0.667, "Ж": 0.923, "К": 0.583, "М": 0.833, "О": 0.778,
   "П": 0.719, "Р": 0.667, "С": 0.722, "У": 0.635, "Ц": 0.740, "Ш": 0.917, "Щ": 0.938,
   "Ы": 0.885, "Ю": 1.010, "а": 0.556, "б": 0.573, "в": 0.531, "г": 0.365, "д": 0.584,
   "е": 0.556, "ж": 0.669, "з": 0.459, "и": 0.559, "й": 0.559, "к": 0.438, "л": 0.584,
   "м": 0.688, "н": 0.552, "о": 0.556, "п": 0.542, "р": 0.556, "с": 0.500, "т": 0.458,
   "у": 0.500, "ф": 0.823, "х": 0.500, "ц": 0.573, "ч": 0.521, "ш": 0.802, "щ": 0.823,
   "ы": 0.719, "ь": 0.521, "э": 0.510, "я": 0.542, "ё": 0.556, "—": 1.000,
}
_W_BOLD = {
   " ": 0.278, "(": 0.333, ")": 0.333, ",": 0.278, "-": 0.333, ".": 0.278, "/": 0.278,
   "0": 0.556, ":": 0.333, "A": 0.722, "C": 0.722, "E": 0.667, "G": 0.778, "H": 0.722,
   "N": 0.722, "O": 0.778, "P": 0.667, "R": 0.722, "S": 0.667, "T": 0.611, "U": 0.722,
   "[": 0.333, "]": 0.333, "a": 0.556, "b": 0.611, "c": 0.556, "d": 0.611, "e": 0.556,
   "f": 0.333, "g": 0.611, "i": 0.278, "l": 0.278, "m": 0.889, "n": 0.611, "o": 0.611,
   "p": 0.611, "r": 0.389, "s": 0.556, "t": 0.333, "u": 0.611, "v": 0.556, "w": 0.778,
   "x": 0.556, "{": 0.389, "}": 0.389, "«": 0.556, "»": 0.556, "А": 0.722, "В": 0.722,
   "Г": 0.567, "Д": 0.712, "Е": 0.667, "Ж": 0.904, "К": 0.610, "М": 0.833, "О": 0.778,
   "П": 0.719, "Р": 0.667, "С": 0.722, "У": 0.622, "Ц": 0.730, "Ш": 1.005, "Щ": 1.019,
   "Ы": 0.979, "Ю": 1.031, "а": 0.556, "б": 0.618, "в": 0.615, "г": 0.417, "д": 0.635,
   "е": 0.556, "ж": 0.709, "з": 0.497, "и": 0.615, "й": 0.615, "к": 0.500, "л": 0.635,
   "м": 0.740, "н": 0.604, "о": 0.611, "п": 0.604, "р": 0.611, "с": 0.556, "т": 0.490,
   "у": 0.556, "ф": 0.875, "х": 0.556, "ц": 0.615, "ч": 0.581, "ш": 0.834, "щ": 0.844,
   "ы": 0.854, "ь": 0.615, "э": 0.552, "я": 0.584, "ё": 0.556, "—": 1.000,
}


def est_w(text, size, bold=False):
    """Ширина строки в px по метрикам Arial (таблица _W_REG/_W_BOLD)."""
    tbl = _W_BOLD if bold else _W_REG
    return sum(tbl.get(ch, 0.60) for ch in text) * size


# ==========================================================================
# построение диаграммы
# ==========================================================================
def actor_label_box(i):
    """Габаритный прямоугольник подписи актёра (для проверки пересечений)."""
    txt = ACTORS[i]
    w = est_w(txt, FS_ACTOR, bold=True)
    y = AY[i]
    return (AX - w / 2 - 2, y + 44, AX + w / 2 + 2, y + 74)


def uc_oval(u):
    name, col, row = UC[u]
    cx = COL1_CX if col == 1 else COL2_CX
    return (cx, ROW_Y[row], RX, RY)


def build():
    s = Svg(W, H)

    # --- заголовок -------------------------------------------------------
    s.text(W / 2, 46, TITLE, size=TITLE_SIZE, weight="bold", fill=C_TITLE)

    # --- линии связи (рисуем до овалов и актёров) ------------------------
    for ai, ucs in sorted(LINKS.items()):
        tx = TRUNK_X[ai]
        # горизонтальная «шина» от фигурки до вертикального ствола
        s.line(SPINE_X0, AY[ai], tx, AY[ai], sw=1.8)
        for u in ucs:
            name, col, row = UC[u]
            ex, ey = entry_point(ai, u)
            if col == 1:
                s.polyline([(tx, ey), (ex + 1, ey)])
            else:
                lane = COL2_LANE[(ai, u)]
                ch = COL2_CH_X[(ai, u)]
                s.polyline([(tx, lane), (ch, lane), (ch, ey), (ex + 1, ey)])

    # --- вертикальные стволы актёров ------------------------------------
    for ai, ucs in sorted(LINKS.items()):
        tx = TRUNK_X[ai]
        ys = [AY[ai]]
        for u in ucs:
            name, col, row = UC[u]
            ys.append(COL2_LANE[(ai, u)] if col == 2 else entry_point(ai, u)[1])
        s.line(tx, min(ys), tx, max(ys), sw=1.8)

    # --- варианты использования -----------------------------------------
    for u in sorted(UC):
        name, col, row = UC[u]
        cx = COL1_CX if col == 1 else COL2_CX
        cy = ROW_Y[row]
        s.ellipse(cx, cy, RX, RY)
        s.text(cx, cy + 9, name, size=FS_UC)

    # --- актёры ----------------------------------------------------------
    for i, name in enumerate(ACTORS):
        y = AY[i]
        s.circle(AX, y - 31, HEAD_R)                       # голова
        s.line(AX, y - 16, AX, y + 18, stroke=C_ACTOR, sw=2.0)          # туловище
        s.line(AX - ARM_HALF, y - 6, AX + ARM_HALF, y - 6,
               stroke=C_ACTOR, sw=2.0)                                     # руки
        s.line(AX, y + 18, AX - LEG_HALF, y + 40, stroke=C_ACTOR, sw=2.0)  # нога
        s.line(AX, y + 18, AX + LEG_HALF, y + 40, stroke=C_ACTOR, sw=2.0)  # нога
        s.text(AX, y + 66, name, size=FS_ACTOR, weight="bold", fill=C_ACTOR_LBL)

    return s


# ==========================================================================
# самопроверка геометрии (без внешних библиотек)
# ==========================================================================
def _seg_points(p1, p2, step=2.0):
    (x1, y1), (x2, y2) = p1, p2
    dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    n = max(2, int(dist / step) + 1)
    return [(x1 + (x2 - x1) * t / n, y1 + (y2 - y1) * t / n) for t in range(n + 1)]


def _inside(px, py, box):
    x0, y0, x1, y1 = box
    return x0 <= px <= x1 and y0 <= py <= y1


def self_check(verbose=True):
    """Проверяет, что линии не идут сквозь овалы и подписи."""
    ovals = [(u, uc_oval(u)) for u in UC]
    labels = [(i, actor_label_box(i)) for i in range(len(ACTORS))]
    title_half = est_w(TITLE, TITLE_SIZE, bold=True) / 2 + 4
    title_box = (W / 2 - title_half, 18, W / 2 + title_half, 52)

    problems = []
    segments = []

    for ai, ucs in LINKS.items():
        tx = TRUNK_X[ai]
        segments.append((f"шина актёра «{ACTORS[ai]}»", (SPINE_X0, AY[ai]), (tx, AY[ai])))
        ys = [AY[ai]]
        for u in ucs:
            name, col, row = UC[u]
            ex, ey = entry_point(ai, u)
            if col == 1:
                segments.append((f"{ACTORS[ai]} -> «{name}»", (tx, ey), (ex + 1, ey)))
            else:
                lane = COL2_LANE[(ai, u)]
                ch = COL2_CH_X[(ai, u)]
                segments.append((f"{ACTORS[ai]} -> «{name}» (1)", (tx, lane), (ch, lane)))
                segments.append((f"{ACTORS[ai]} -> «{name}» (2)", (ch, lane), (ch, ey)))
                segments.append((f"{ACTORS[ai]} -> «{name}» (3)", (ch, ey), (ex + 1, ey)))
            ys.append(lane if col == 2 else ey)
        segments.append((f"ствол актёра «{ACTORS[ai]}»", (tx, min(ys)), (tx, max(ys))))

    margin = 6.0
    for label, p1, p2 in segments:
        for px, py in _seg_points(p1, p2):
            for u, (cx, cy, rx, ry) in ovals:
                if ((px - cx) / (rx - margin)) ** 2 + ((py - cy) / (ry - margin)) ** 2 < 1.0:
                    problems.append(f"линия «{label}» заходит внутрь овала «{UC[u][0]}»")
            for i, box in labels:
                if _inside(px, py, box):
                    problems.append(f"линия «{label}» пересекает подпись актёра «{ACTORS[i]}»")
            if _inside(px, py, title_box):
                problems.append(f"линия «{label}» пересекает заголовок")

    # текст вариантов использования должен помещаться в овал
    for u in sorted(UC):
        name, col, row = UC[u]
        need = est_w(name, FS_UC) + 34
        avail = 2 * (RX - 6) * (1 - (13.0 / RY) ** 2) ** 0.5
        if need > avail:
            problems.append(f"текст «{name}» ({need:.0f} px) не помещается в овал ({avail:.0f} px)")

    # подписи актёров не должны залезать в коридор стволов
    for i in range(len(ACTORS)):
        if actor_label_box(i)[2] > min(TRUNK_X) - 6:
            problems.append(f"подпись актёра «{ACTORS[i]}» заходит в коридор линий")

    # линии не должны накладываться друг на друга (совпадать на отрезке)
    for i in range(len(segments)):
        l1, (ax, ay), (bx, by) = segments[i]
        for j in range(i + 1, len(segments)):
            l2, (cx, cy), (dx, dy) = segments[j]
            if ay == by == cy == dy:                       # обе горизонтальны
                a0, a1 = sorted([ax, bx])
                c0, c1 = sorted([cx, dx])
            elif ax == bx == cx == dx:                     # обе вертикальны
                a0, a1 = sorted([ay, by])
                c0, c1 = sorted([cy, dy])
            else:
                continue
            ov = min(a1, c1) - max(a0, c0)
            if ov > 1.0:
                problems.append(f"линии совпадают на участке длиной {ov:.0f} px: "
                                f"«{l1}» и «{l2}»")

    if verbose:
        if problems:
            print("САМОПРОВЕРКА: найдены проблемы:")
            for p in dict.fromkeys(problems):
                print("  -", p)
        else:
            print("Самопроверка геометрии: наложений линий на овалы и подписи нет.")
    return problems


# ==========================================================================
def main():
    os.makedirs(OUT, exist_ok=True)
    svg_path = os.path.join(OUT, SVG_NAME)
    png_path = os.path.join(OUT, PNG_NAME)

    build().save(svg_path)
    print("SVG:", svg_path)

    problems = self_check()

    try:
        subprocess.run(["rsvg-convert", "-w", str(W), svg_path, "-o", png_path],
                       check=True)
        print("PNG:", png_path)
    except FileNotFoundError:
        print("rsvg-convert не найден — PNG не создан", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print("rsvg-convert завершился с ошибкой:", e, file=sys.stderr)
        return 1
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
