#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — диаграмма вариантов использования (переработанная разводка линий).

Создаёт:
    diagrams/08b_use_case.svg
    diagrams/08b_use_case.png      (rsvg-convert -w 1700 ...)

Что изменилось по сравнению с предыдущей версией
------------------------------------------------
Предыдущая версия рисовала по одной вертикальной «шине» на каждого актёра,
причём шины стояли вплотную (шаг 25 px) и тянулись через всю высоту схемы.
Вместе с длинными горизонтальными подводками это давало «паутину», в которой
связь «актёр → прецедент» невозможно проследить.

Новая разводка:
  * Коридор стволов 390…570 px, шаг ровно 30 px (было 25 px) — каждый актёр
    получил собственный вертикальный коридор, а стволы стали короткими:
    ствол тянется только от фигурки актёра до самой дальней его подводки,
    а не через всю схему.
  * Горизонтальные подводки к овалам левой колонки лежат ровно на уровне
    точки входа в овал и идут в свободном коридоре левее овалов.
  * Подводки к правой колонке идут по свободной горизонтальной полосе
    между строками овалов (полоса не задевает ни один овал), затем по
    короткому вертикальному каналу в промежутке между колонками и только
    потом входят в овал. Каналы разнесены по трём позициям (1108/1140/1172)
    и имеют разную высоту, поэтому не сливаются в пучок.
  * Число связей сокращено с 30 до 15: у каждого актёра 2–3 ключевых
    прецедента вместо 4–5 (см. LINKS). Полнота принесена в жертву
    читаемости — как и требует задача.
  * Если в прецедент входят несколько актёров, точки входа разведены по
    левой дуге овала (ENTRY_DY), поэтому линии не сливаются в одну.

Итог: 15 связей, ни одного наложения линий, 11 ортогональных пересечений
(все — чистые пересечения под 90°, без «пучков»). Проверяется функцией
self_check() при каждой генерации.

Компоновка сохранена по требованиям: 7 актёров слева, 12 прецедентов в двух
колонках, все подписи >= 26 px, полотно 1700x950.

Источник ролей и прецедентов: docs/01_ТЗ_постановка_задачи.md,
разделы 1.4 «Роли пользователей и их задачи» и 1.5 «Функциональные
требования» (подсистемы 1.5.1–1.5.6).

Запуск:  python3 tools/gen_usecase_v2.py
"""

import math
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

# актёры: фигурки в один столбец слева
AX = 185                    # центр фигурки по X
AY0, AY_STEP = 126, 118     # центр фигурки по Y (7 актёров)
LABEL_DY = 62               # базовая линия подписи актёра относительно центра
HEAD_R = 15
ARM_HALF = 34
LEG_HALF = 24
SPINE_X0 = AX + ARM_HALF    # 219 — начало горизонтальной «шины» актёра

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

# овалы прецедентов: две колонки по 6
ROW_Y0, ROW_STEP = 132, 146
ROW_Y = [ROW_Y0 + r * ROW_STEP for r in range(6)]
RX, RY = 248, 48            # овал 496 x 96
COL1_CX, COL2_CX = 848, 1437
COL1_L, COL1_R = COL1_CX - RX, COL1_CX + RX     # 600 … 1096
COL2_L, COL2_R = COL2_CX - RX, COL2_CX + RX     # 1189 … 1685

# id прецедента -> подпись
UC_NAME = {
    1: "Приём и регистрация заявок",
    2: "Подбор и бронирование техники",
    3: "Оформление договоров аренды",
    4: "Выдача и возврат техники",
    5: "Регистрация платежей",
    6: "Учёт экземпляров техники",
    7: "Учёт состояния техники",
    8: "Ведение обслуживания и ремонта",
    9: "Подача заявки вузом",
    10: "Просмотр своих заявок и договоров",
    11: "Ведение номенклатуры и тарифов",
    12: "Сводные отчёты по сети",
}
# порядок прецедентов сверху вниз в каждой колонке
LEFT_ORDER = [1, 2, 3, 4, 5, 6]
RIGHT_ORDER = [7, 8, 10, 9, 12, 11]

UC = {}
for _i, _u in enumerate(LEFT_ORDER):
    UC[_u] = (UC_NAME[_u], 1, _i)
for _i, _u in enumerate(RIGHT_ORDER):
    UC[_u] = (UC_NAME[_u], 2, _i)

# --------------------------------------------------------------------------
# связи «актёр → прецедент».
# В исходном ТЗ у менеджера было 5 прецедентов, у склада — 4 и т.д.
# Для читаемости оставлены 2–3 ключевых на каждого актёра (15 связей),
# при этом все 12 прецедентов остались связаны хотя бы с одним актёром.
# --------------------------------------------------------------------------
LINKS = {
    0: [1, 2, 3],       # Менеджер филиала:   приём заявок, подбор/бронирование, договоры
    1: [2, 4],          # Сотрудник склада:   подбор/бронирование, выдача и возврат
    2: [7, 8],          # Специалист сервиса: состояние техники, обслуживание и ремонт
    3: [1, 12],         # Руководитель филиала: контроль заявок, сводные отчёты
    4: [9, 10],         # Представитель вуза: подача заявки, просмотр своих заявок
    5: [6, 11],         # Сотрудник ЦО:       учёт экземпляров, номенклатура и тарифы
    6: [5, 12],         # Руководство и бухгалтерия: платежи, сводные отчёты
}

# Вертикальные стволы актёров: слоты 390…570 с шагом 30 px.
# Порядок слотов подобран так, чтобы пересечений было минимум
# (см. TRUNK_X: у кого подводки длиннее — тот стоит правее).
TRUNK_SLOTS = [390 + 30 * i for i in range(len(ACTORS))]
TRUNK_X = {0: 540, 1: 480, 2: 510, 3: 420, 4: 570, 5: 450, 6: 390}

# Свободная горизонтальная полоса для подводки к правой колонке:
#   b — номер зазора между строками (b и b+1), lane лежит внутри зазора.
LANE_BAND = {
    (2, 7): 1, (2, 8): 1, (3, 12): 3, (4, 9): 4, (4, 10): 2,
    (5, 11): 4, (6, 12): 3,
}
LANE_MARGIN = 8             # отступ полосы от обводки овалов

# Вертикальный канал в промежутке между колонками (1096…1189).
CH_X = {
    (2, 7): 1172, (2, 8): 1108, (3, 12): 1172, (4, 9): 1140,
    (4, 10): 1172, (5, 11): 1140, (6, 12): 1140,
}
CH_SLOTS = sorted(set(CH_X.values()))

# Точки входа в овал при нескольких актёрах: тому, чей ствол правее,
# достаётся верхняя точка левой дуги (иначе его ствол перерезал бы
# горизонтальную подводку соседа).
ENTRY_DY = {1: [0.0], 2: [-26.0, 26.0], 3: [-26.0, 0.0, 26.0]}


def uc_actors(u):
    """Актёры, связанные с прецедентом, — от правого ствола к левому."""
    return sorted([a for a in LINKS if u in LINKS[a]], key=lambda a: -TRUNK_X[a])


def entry_points():
    """(актёр, прецедент) -> (x, y) точки входа в овал."""
    res = {}
    for u, (_, col, row) in UC.items():
        actors = uc_actors(u)
        dys = ENTRY_DY.get(len(actors))
        if dys is None:
            step = 52.0 / max(1, len(actors) - 1)
            dys = [-26 + step * k for k in range(len(actors))]
        cx = COL1_CX if col == 1 else COL2_CX
        for a, dy in zip(actors, dys):
            dx = RX * math.sqrt(max(0.0, 1.0 - (dy / RY) ** 2))
            res[(a, u)] = (cx - dx, ROW_Y[row] + dy)
    return res


def lane_ys():
    """(актёр, прецедент) -> y горизонтальной полосы для правой колонки."""
    band_items = {}
    for a in sorted(LINKS):
        for u in LINKS[a]:
            if UC[u][1] == 2:
                band_items.setdefault(LANE_BAND[(a, u)], []).append((a, u, UC[u][2]))
    res = {}
    for b, items in band_items.items():
        if len(items) > 2:
            raise ValueError("в зазоре %d больше двух подводок" % b)
        items.sort(key=lambda t: (t[2], t[0]))
        lo = ROW_Y[b] + RY + LANE_MARGIN
        hi = ROW_Y[b + 1] - RY - LANE_MARGIN
        ys = [(lo + hi) / 2] if len(items) == 1 else [lo, hi]
        for (a, u, _row), y in zip(items, ys):
            res[(a, u)] = y
    return res


ENTRIES = entry_points()
LANES = lane_ys()


def connection_path(a, u):
    """Ломаная «ствол актёра → овал прецедента»."""
    tx = TRUNK_X[a]
    ex, ey = ENTRIES[(a, u)]
    if UC[u][1] == 1:
        return [(tx, ey), (ex + 1, ey)]
    ly = LANES[(a, u)]
    ch = CH_X[(a, u)]
    return [(tx, ly), (ch, ly), (ch, ey), (ex + 1, ey)]


def trunk_span(a):
    """(y_min, y_max) вертикального ствола актёра."""
    ys = [AY[a]]
    for u in LINKS[a]:
        ys.append(ENTRIES[(a, u)][1] if UC[u][1] == 1 else LANES[(a, u)])
    return min(ys), max(ys)


def spine(a):
    return [(SPINE_X0, AY[a]), (TRUNK_X[a], AY[a])]


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

    def line(self, x1, y1, x2, y2, stroke=C_LINK, sw=2.2, cap="round"):
        self.raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="{cap}"/>')

    def polyline(self, pts, stroke=C_LINK, sw=2.2):
        p = " ".join(f"{round(x, 1)},{round(y, 1)}" for (x, y) in pts)
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
        self.raw(f'<text x="{round(x, 1)}" y="{round(y, 1)}" font-family="{FONT}" '
                 f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
                 f'fill="{fill}">{esc(s)}</text>')

    def save(self, path):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="{C_BG}"/>')
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n" + "\n".join(self.parts) + "\n</svg>\n")


# ==========================================================================
# приблизительная ширина текста (для самопроверки, метрики Arial)
# ==========================================================================
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
    tbl = _W_BOLD if bold else _W_REG
    return sum(tbl.get(ch, 0.60) for ch in text) * size


def actor_label_box(i):
    """Габаритный прямоугольник подписи актёра."""
    w = est_w(ACTORS[i], FS_ACTOR, bold=True)
    y = AY[i] + LABEL_DY
    return (AX - w / 2 - 2, y - 22, AX + w / 2 + 2, y + 8)


def title_box():
    half = est_w(TITLE, TITLE_SIZE, bold=True) / 2 + 4
    return (W / 2 - half, 16, W / 2 + half, 54)


# ==========================================================================
# построение диаграммы
# ==========================================================================
def build():
    s = Svg(W, H)
    s.text(W / 2, 46, TITLE, size=TITLE_SIZE, weight="bold", fill=C_TITLE)

    # линии связи (рисуем под овалами и фигурками)
    for ai in sorted(LINKS):
        s.polyline(spine(ai))
        y0, y1 = trunk_span(ai)
        s.line(TRUNK_X[ai], y0, TRUNK_X[ai], y1)
        for u in LINKS[ai]:
            s.polyline(connection_path(ai, u))

    # варианты использования
    for u in sorted(UC):
        name, col, row = UC[u]
        cx = COL1_CX if col == 1 else COL2_CX
        s.ellipse(cx, ROW_Y[row], RX, RY)
        s.text(cx, ROW_Y[row] + 9, name, size=FS_UC)

    # актёры
    for i, name in enumerate(ACTORS):
        y = AY[i]
        s.circle(AX, y - 31, HEAD_R)
        s.line(AX, y - 16, AX, y + 18, stroke=C_ACTOR, sw=2.0)
        s.line(AX - ARM_HALF, y - 6, AX + ARM_HALF, y - 6, stroke=C_ACTOR, sw=2.0)
        s.line(AX, y + 18, AX - LEG_HALF, y + 40, stroke=C_ACTOR, sw=2.0)
        s.line(AX, y + 18, AX + LEG_HALF, y + 40, stroke=C_ACTOR, sw=2.0)
        s.text(AX, y + LABEL_DY, name, size=FS_ACTOR, weight="bold",
               fill=C_ACTOR_LBL)
    return s


# ==========================================================================
# самопроверка геометрии (без внешних библиотек)
# ==========================================================================
def _segments():
    """Все отрезки схемы: (подпись, владелец, (x1,y1), (x2,y2))."""
    segs = []
    for ai in sorted(LINKS):
        pts = spine(ai)
        segs.append((f"шина «{ACTORS[ai]}»", ai, pts[0], pts[1]))
        y0, y1 = trunk_span(ai)
        segs.append((f"ствол «{ACTORS[ai]}»", ai, (TRUNK_X[ai], y0), (TRUNK_X[ai], y1)))
        for u in LINKS[ai]:
            path = connection_path(ai, u)
            for k in range(len(path) - 1):
                segs.append((f"{ACTORS[ai]} → «{UC_NAME[u]}»",
                             ai, path[k], path[k + 1]))
    return segs


def _clip_seg_ellipse(p1, p2, cx, cy, rx, ry):
    """Длина перекрытия отрезка с внутренностью эллипса."""
    (x1, y1), (x2, y2) = p1, p2
    if x1 == x2:
        if abs(x1 - cx) >= rx:
            return 0.0
        d = ry * math.sqrt(1 - ((x1 - cx) / rx) ** 2)
        return max(0.0, min(max(y1, y2), cy + d) - max(min(y1, y2), cy - d))
    if abs(y1 - cy) >= ry:
        return 0.0
    d = rx * math.sqrt(1 - ((y1 - cy) / ry) ** 2)
    return max(0.0, min(max(x1, x2), cx + d) - max(min(x1, x2), cx - d))


def _inside(px, py, box):
    x0, y0, x1, y1 = box
    return x0 <= px <= x1 and y0 <= py <= y1


def _pair_relation(p1, p2, p3, p4):
    """cross / touch / overlap / close / None для двух ортогональных отрезков."""
    (x1, y1), (x2, y2) = p1, p2
    (x3, y3), (x4, y4) = p3, p4
    v1, v2 = x1 == x2, x3 == x4
    if v1 and v2:
        if x1 == x3:
            a0, a1 = sorted([y1, y2])
            b0, b1 = sorted([y3, y4])
            ov = min(a1, b1) - max(a0, b0)
            return "overlap" if ov > 2 else ("touch" if ov > -2 else None)
        if abs(x1 - x3) < 26:
            a0, a1 = sorted([y1, y2])
            b0, b1 = sorted([y3, y4])
            if min(a1, b1) - max(a0, b0) > 20:
                return "close"
        return None
    if (not v1) and (not v2):
        if y1 == y3:
            a0, a1 = sorted([x1, x2])
            b0, b1 = sorted([x3, x4])
            ov = min(a1, b1) - max(a0, b0)
            return "overlap" if ov > 2 else ("touch" if ov > -2 else None)
        if abs(y1 - y3) < 26:
            a0, a1 = sorted([x1, x2])
            b0, b1 = sorted([x3, x4])
            if min(a1, b1) - max(a0, b0) > 20:
                return "close"
        return None
    if v1:
        xv, yv0, yv1 = x1, *sorted([y1, y2])
        yh, xh0, xh1 = y3, *sorted([x3, x4])
    else:
        xv, yv0, yv1 = x3, *sorted([y3, y4])
        yh, xh0, xh1 = y1, *sorted([x1, x2])
    if xh0 < xv < xh1 and yv0 < yh < yv1:
        return "cross"
    if xh0 <= xv <= xh1 and yv0 <= yh <= yv1:
        return "touch"
    return None


def self_check(verbose=True):
    problems = []
    segs = _segments()

    # 1. линии не заходят внутрь овалов
    for label, owner, p1, p2 in segs:
        for u, (_, col, row) in UC.items():
            cx = COL1_CX if col == 1 else COL2_CX
            if _clip_seg_ellipse(p1, p2, cx, ROW_Y[row], RX - 4, RY - 4) > 0.5:
                problems.append(f"линия «{label}» заходит внутрь овала «{UC_NAME[u]}»")

    # 2. линии не пересекают подписи актёров и заголовок
    for label, owner, p1, p2 in segs:
        (x1, y1), (x2, y2) = p1, p2
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 3) + 1)
        for t in range(n + 1):
            px = x1 + (x2 - x1) * t / n
            py = y1 + (y2 - y1) * t / n
            for i in range(len(ACTORS)):
                if _inside(px, py, actor_label_box(i)):
                    problems.append(f"линия «{label}» пересекает подпись актёра "
                                    f"«{ACTORS[i]}»")
            if _inside(px, py, title_box()):
                problems.append(f"линия «{label}» пересекает заголовок")

    # 3/4. взаимные наложения, касания и пересечения линий
    crossings = []
    for i in range(len(segs)):
        l1, a1, p1, p2 = segs[i]
        for j in range(i + 1, len(segs)):
            l2, a2, p3, p4 = segs[j]
            rel = _pair_relation(p1, p2, p3, p4)
            if rel == "overlap":
                problems.append(f"линии совпадают: «{l1}» и «{l2}»")
            elif rel == "close":
                problems.append(f"параллельные линии ближе 26 px: «{l1}» и «{l2}»")
            elif rel == "touch" and a1 != a2:
                problems.append(f"линия «{l2}» упирается в «{l1}» (T-образный стык)")
            elif rel == "cross":
                crossings.append((l1, l2))

    # 5. вертикальные стволы стоят не ближе 26 px друг к другу
    spans = {a: trunk_span(a) for a in sorted(LINKS)}
    for i in sorted(LINKS):
        for j in sorted(LINKS):
            if i >= j:
                continue
            ov = min(spans[i][1], spans[j][1]) - max(spans[i][0], spans[j][0])
            gap = abs(TRUNK_X[i] - TRUNK_X[j])
            if ov > 20 and gap < 26:
                problems.append(f"стволы «{ACTORS[i]}» и «{ACTORS[j]}» ближе 26 px")

    # 6. текст прецедентов помещается в овал
    for u in sorted(UC):
        need = est_w(UC_NAME[u], FS_UC) + 22
        avail = 2 * (RX - 6) * math.sqrt(1 - (13.0 / RY) ** 2)
        if need > avail:
            problems.append(f"текст «{UC_NAME[u]}» ({need:.0f} px) не помещается "
                            f"в овал ({avail:.0f} px)")

    # 7. каждый прецедент связан хотя бы с одним актёром, у каждого актёра >= 2
    for u in sorted(UC):
        if not uc_actors(u):
            problems.append(f"у прецедента «{UC_NAME[u]}» нет ни одного актёра")
    for a in sorted(LINKS):
        if len(LINKS[a]) < 2:
            problems.append(f"у актёра «{ACTORS[a]}» меньше двух прецедентов")

    # 8. подписи актёров не заходят в коридор стволов
    for i in range(len(ACTORS)):
        if actor_label_box(i)[2] > min(TRUNK_SLOTS) - 6:
            problems.append(f"подпись актёра «{ACTORS[i]}» заходит в коридор линий")

    if verbose:
        if problems:
            print("САМОПРОВЕРКА: найдены проблемы:")
            for p in dict.fromkeys(problems):
                print("  -", p)
        else:
            print("Самопроверка: наложений линий на овалы, подписи и друг на "
                  "друга нет; T-стыков нет.")
        print(f"Пересечений линий (ортогональных, под 90°): {len(crossings)}")
        for l1, l2 in crossings:
            print(f"  · «{l1}» × «{l2}»")
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
