#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — ER-диаграммы в нотации «вороньи лапки» (crow's foot) для презентации.

Создаёт файлы в каталоге diagrams/:
  09_er_notation.svg/.png           — нотация связей: 1:1, 1:N, M:N и как читать символы
  10_er_crowsfoot_clients.svg/.png  — подсистема «НСИ, клиенты, персонал» (10 таблиц)
  11_er_crowsfoot_rental.svg/.png   — подсистема «Техника, аренда, сервис» (12 таблиц)

Читаемость на слайде (важно!).
  Диаграмма вставляется в слайд 1280x720 в рамку 900x575 (fit: contain), т.е. PNG
  шириной 1700 px показывается шириной ~830 px — коэффициент 0,487. Поэтому кегли
  подняты так, чтобы на слайде получилось >= 15 px:
      атрибуты        32 px  -> ~15,6 px на слайде
      заголовки       34 px  -> ~16,6 px
      легенда         28 px  -> ~13,6 px
      кардинальности  28 px  -> ~13,6 px
      сноска          28 px  -> ~13,6 px
  Чтобы это поместилось, убраны отступы, тип поля вынесен в отчёт (в ER остаются
  только PK/FK и ключевые атрибуты), а скрытые поля помечены строкой «… ещё N полей».

Особенности реализации:
  * чистый Python + SVG, без внешних библиотек (Pillow используется только для
    точного контроля ширины строк, если он доступен);
  * координаты плашек подобраны вручную; связи — ортогональные ломаные по свободным
    «коридорам» между плашками, поэтому линии не проходят сквозь таблицы;
  * встроенная проверка QA: каждый отрезок связи проверяется на пересечение с
    прямоугольниками таблиц, каждая подпись — на попадание в плашку и на чужие линии.

Запуск:  python3 tools/gen_er_crowsfoot.py
         (SVG пишутся всегда; PNG — через rsvg-convert -w 1700, если он есть в PATH)

Проверка «как на слайде»:
    rsvg-convert -w 807 diagrams/10_er_crowsfoot_clients.svg -o /tmp/slide10.png
"""

import math
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "diagrams")

FONT = "Helvetica, Arial, sans-serif"

# ---------------------------------------------------------------------------
# Палитра (взята из tools/gen_diagrams.py)
# ---------------------------------------------------------------------------
C_LINE = "#1f2937"
C_TXT = "#111827"
C_SUB = "#4b5563"
C_GRAY = "#6b7280"
C_SOFT = "#e5e7eb"

P_NSI = ("#dbeafe", "#1d4ed8")     # НСИ — синий
P_CLI = ("#dcfce7", "#15803d")     # клиенты — зелёный
P_EQ = ("#fef9c3", "#a16207")      # техника — жёлтый
P_REQ = ("#fee2e2", "#b91c1c")     # заявки / аренда — красный
P_CTR = ("#ffedd5", "#c2410c")     # договоры / финансы / сервис — оранжевый
P_HQ = ("#e0e7ff", "#3730a3")      # филиалы и персонал — индиго

# ---------------------------------------------------------------------------
# Геометрия и кегли
# ---------------------------------------------------------------------------
CANVAS_W = 1700
CANVAS_H = 1180
TBL_W = 352          # ширина плашки таблицы на ER-диаграммах
BADGE_X = 14         # левый край метки PK/FK
NAME_X = 64          # левый край имени поля
COLS = (29, 459, 889, 1319)   # левые края четырёх колонок

HDR_H = 80           # высота шапки таблицы
LINE_H = 36          # шаг строки полей
PAD_TOP = 10
PAD_BOT = 8
ROW_GAP = 60         # вертикальный коридор между рядами таблиц

BAR_D = 22           # расстояние от плашки до черты «один»
BAR_HH = 15          # половина длины черты «один»
CF_APEX = 26         # расстояние от плашки до вершины «вороньей лапки»
CF_SPREAD = 16       # половина раствора «вороньей лапки»
CIRC_D = 38          # расстояние от плашки до кружка «необязательно»
CIRC_R = 9

SW_LINE = 2.4
SW_SYM = 2.6
SW_BOX = 2.4

# Кегли: атрибуты >= 32, заголовки >= 34, кардинальности/легенда >= 28
FS_TXT = 32          # атрибуты
FS_HDR = 34          # заголовок таблицы
FS_EN = 26           # английское имя сущности (диаграмма нотации)
FS_TBL_EN = 28       # английское имя таблицы на ER-диаграммах
FS_CARD = 28         # подписи кардинальностей «1»/«N»/«0..1»
FS_LEG = 28          # легенда
FS_NOTE = 28         # сноска
FS_TITLE = 38        # заголовок диаграммы
FS_SUB = 28          # подзаголовок диаграммы
FS_ENT = 32          # имя сущности на диаграмме нотации

# ---------------------------------------------------------------------------
# Оценка ширины строки — контроль переполнения.
# Если доступен Pillow, метрики берутся из того же Helvetica, которым рисует
# rsvg-convert; иначе — грубая оценка.
# ---------------------------------------------------------------------------
_W_NARROW = set("iljI.,:;!|'`()[]{}-/\\ft ")
_W_WIDE = set("MW@ШЩЖЮФМmw")

try:                                        # pragma: no cover
    from PIL import ImageFont as _ImageFont
    _FONT_CACHE = {}

    def _pil(size, style):
        key = (size, style)
        f = _FONT_CACHE.get(key)
        if f is None:
            idx = 0 if style == "regular" else (1 if style == "bold" else 2)
            f = _ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",
                                    size, index=idx)
            _FONT_CACHE[key] = f
        return f

    def text_w(text, size, style="regular"):
        """Ширина строки в пикселях (с запасом 2 %)."""
        return _pil(size, style).getlength(text) * 1.02
except Exception:                           # pragma: no cover
    def text_w(text, size, style="regular"):
        w = 0.0
        for ch in text:
            if ch in _W_NARROW:
                w += 0.34
            elif ch in _W_WIDE:
                w += 0.90
            elif ch.isdigit():
                w += 0.56
            elif ch.isupper():
                w += 0.70
            else:
                w += 0.56
        return w * size


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------
class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=C_LINE, sw=1.5, rx=8, dash=None):
        d = ' stroke-dasharray="9 7"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=FS_TXT, anchor="middle", weight="normal",
             fill=C_TXT, italic=False):
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{st}>'
                 f'{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=C_LINE, sw=SW_LINE, dash=None):
        d = ' stroke-dasharray="9 7"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="round"{d}/>')

    def polyline(self, pts, stroke=C_LINE, sw=SW_LINE, dash=None):
        d = ' stroke-dasharray="9 7"' if dash else ""
        p = " ".join(f"{x},{y}" for (x, y) in pts)
        self.add(f'<polyline points="{p}" fill="none" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def circle(self, cx, cy, r, fill="#ffffff", stroke=C_LINE, sw=SW_SYM):
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<title>{esc(self.title)}</title>'
                f'<rect width="100%" height="100%" fill="#ffffff"/>')
        body = "\n".join(self.parts)
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n" + body + "\n</svg>\n")
        return path

    def header(self, title, subtitle=None):
        self.text(30, 52, title, size=FS_TITLE, anchor="start", weight="bold")
        if text_w(title, FS_TITLE, "bold") + 34 > self.w:
            QA_WARNS.append("заголовок шире полотна: «%s»" % title)
        if subtitle:
            self.text(30, 90, subtitle, size=FS_SUB, anchor="start", fill=C_SUB)
            if text_w(subtitle, FS_SUB) + 34 > self.w:
                QA_WARNS.append("подзаголовок шире полотна: «%s»" % subtitle)


def wrap(text, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Таблицы
# ---------------------------------------------------------------------------
def fy(t, i):
    """Y середины i-й строки полей."""
    return t["y"] + HDR_H + PAD_TOP + i * LINE_H + LINE_H / 2.0


def tbl_h(n_rows):
    return HDR_H + PAD_TOP + n_rows * LINE_H + PAD_BOT


def L(t, y):
    return (t["x"], y)


def R(t, y):
    return (t["x"] + TBL_W, y)


def T(t, x):
    return (x, t["y"])


def B(t, x):
    return (x, t["y"] + t["h"])


def elide(n):
    """Строка «… ещё N полей» вместо скрытых неключевых полей."""
    if n % 10 == 1 and n % 100 != 11:
        word = "поле"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        word = "поля"
    else:
        word = "полей"
    return ("ELIDE", "ещё %d %s" % (n, word))


def make_table(key, ru, en, row, col, pal, fields):
    """fields: [(badge, name)], badge: PK | FK | FKX | ''."""
    return {"key": key, "ru": ru, "en": en, "row": row, "col": col, "pal": pal,
            "fields": fields, "h": tbl_h(len(fields))}


def place_tables(tables, y0=126, gap=ROW_GAP):
    by_row = {}
    for t in tables.values():
        by_row.setdefault(t["row"], []).append(t["h"])
    y, ys = y0, {}
    for r in sorted(by_row):
        ys[r] = y
        y += max(by_row[r]) + gap
    for t in tables.values():
        t["x"] = COLS[t["col"]]
        t["y"] = ys[t["row"]]
    return y - gap      # нижняя граница таблиц


def draw_table(s, t, qa_boxes, qa_warns):
    x, y, w, h = t["x"], t["y"], TBL_W, t["h"]
    fill, stroke = t["pal"]
    s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=SW_BOX, rx=10)
    s.line(x, y + HDR_H, x + w, y + HDR_H, stroke=stroke, sw=2.2)
    s.text(x + 16, y + 38, t["ru"], size=FS_HDR, anchor="start", weight="bold",
           fill=stroke)
    s.text(x + 16, y + 70, t["en"], size=FS_TBL_EN, anchor="start", fill=C_GRAY,
           italic=True)
    if text_w(t["ru"], FS_HDR, "bold") + 32 > w:
        qa_warns.append("%s: заголовок «%s» шире плашки" % (t["key"], t["ru"]))
    if text_w(t["en"], FS_TBL_EN, "italic") + 32 > w:
        qa_warns.append("%s: англ. имя «%s» шире плашки" % (t["key"], t["en"]))
    for i, f in enumerate(t["fields"]):
        by = y + HDR_H + PAD_TOP + i * LINE_H + 25
        if f[0] == "ELIDE":
            s.text(x + BADGE_X, by, "…", size=FS_TXT, anchor="start", weight="bold",
                   fill=C_GRAY)
            s.text(x + NAME_X, by, f[1], size=FS_TXT, anchor="start", fill=C_GRAY,
                   italic=True)
            continue
        badge, name = f
        if badge == "PK":
            s.text(x + BADGE_X, by, "PK", size=FS_TXT, anchor="start", weight="bold",
                   fill=C_LINE)
            s.text(x + NAME_X, by, name, size=FS_TXT, anchor="start", weight="bold")
        elif badge == "FK":
            s.text(x + BADGE_X, by, "FK", size=FS_TXT, anchor="start", weight="bold",
                   fill=C_LINE)
            s.text(x + NAME_X, by, name, size=FS_TXT, anchor="start")
        elif badge == "FKX":
            s.text(x + BADGE_X, by, "FK", size=FS_TXT, anchor="start", weight="bold",
                   fill=C_GRAY)
            s.text(x + NAME_X, by, name + " ↗", size=FS_TXT, anchor="start",
                   fill=C_GRAY)
        else:
            s.text(x + NAME_X, by, name, size=FS_TXT, anchor="start")
        used = NAME_X + text_w(name, FS_TXT) + 8
        if badge == "FKX":
            used += text_w(" ↗", FS_TXT)
        if used > w:
            qa_warns.append("%s: строка «%s» шире плашки (%.0f > %d)"
                            % (t["key"], name, used, w))
    qa_boxes.append((t["key"], x, y, w, h))


def draw_ent(s, x, y, w, h, ru, en, pal, qa_boxes=None, key=None):
    """Плашка сущности для диаграммы нотации (без списка полей)."""
    fill, stroke = pal
    s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=SW_BOX, rx=10)
    s.text(x + w / 2, y + h / 2 - 4, ru, size=FS_ENT, weight="bold", fill=stroke)
    s.text(x + w / 2, y + h / 2 + 24, en, size=FS_EN, fill=C_GRAY, italic=True)
    if qa_boxes is not None:
        qa_boxes.append((key or ru, x, y, w, h))


# ---------------------------------------------------------------------------
# Символы нотации «вороньи лапки»
#   (dx, dy) — единичное направление ОТ плашки вдоль линии связи
# ---------------------------------------------------------------------------
def sym_one(s, x, y, dx, dy, color=C_LINE):
    """Одна черта — «ровно один»."""
    bx, by = x + dx * BAR_D, y + dy * BAR_D
    px, py = -dy, dx
    s.line(bx - px * BAR_HH, by - py * BAR_HH, bx + px * BAR_HH, by + py * BAR_HH,
           stroke=color, sw=SW_SYM)


def sym_many(s, x, y, dx, dy, color=C_LINE):
    """Три расходящиеся линии — «многие»."""
    ax, ay = x + dx * CF_APEX, y + dy * CF_APEX
    px, py = -dy, dx
    for k in (-1, 1):
        s.line(x + px * CF_SPREAD * k, y + py * CF_SPREAD * k, ax, ay,
               stroke=color, sw=SW_SYM)


def sym_circle(s, x, y, dx, dy, rmul=1.0, color=C_LINE):
    """Кружок — «необязательная связь» (может не быть ни одного экземпляра)."""
    s.circle(x + dx * CIRC_D * rmul, y + dy * CIRC_D * rmul, CIRC_R,
             fill="#ffffff", stroke=color, sw=SW_SYM)


# ---------------------------------------------------------------------------
# Связь + сбор данных для QA
# ---------------------------------------------------------------------------
QA_BOXES = []
QA_SEGS = []
QA_LABELS = []
QA_WARNS = []


def _unit(vx, vy):
    n = math.hypot(vx, vy)
    if n == 0:
        return 1.0, 0.0
    return vx / n, vy / n


def edge(s, name, path, many=True, dash=False, labels=(), color=C_LINE):
    """Связь от стороны «один» (path[0]) к стороне «многие» (path[-1]).

    many=False — связь 1:1 (черта с двух сторон, без «вороньей лапки»).
    labels — список (текст, x, y[, anchor]).
    """
    path = [(float(a), float(b)) for (a, b) in path]
    dx, dy = _unit(path[1][0] - path[0][0], path[1][1] - path[0][1])
    s.polyline(path, stroke=color, sw=SW_LINE, dash=dash)
    sym_one(s, path[0][0], path[0][1], dx, dy, color)
    if many:
        ex, ey = path[-1]
        edx, edy = _unit(path[-2][0] - ex, path[-2][1] - ey)
        sym_many(s, ex, ey, edx, edy, color)
    else:
        ex, ey = path[-1]
        edx, edy = _unit(path[-2][0] - ex, path[-2][1] - ey)
        sym_one(s, ex, ey, edx, edy, color)
    QA_SEGS.append((name, path))
    for lab in labels:
        anchor = lab[3] if len(lab) > 3 else "middle"
        card(s, lab[0], lab[1], lab[2], anchor)


def card(s, txt, x, y, anchor="middle", color=C_LINE):
    """Подпись кардинальности + регистрация в QA."""
    s.text(x, y, txt, size=FS_CARD, anchor=anchor, weight="bold", fill=color)
    w = text_w(txt, FS_CARD, "bold")
    cx = x if anchor == "middle" else (x + w / 2.0 if anchor == "start"
                                       else x - w / 2.0)
    QA_LABELS.append((txt, cx, y - 9, w, 22))


# ---------------------------------------------------------------------------
# Проверки QA
# ---------------------------------------------------------------------------
def seg_rect_hit(p, q, rx, ry, rw, rh, inset=3.0):
    """Пересекает ли отрезок p-q внутренность прямоугольника (Liang–Barsky)."""
    x1, y1 = p
    x2, y2 = q
    xmin, ymin = rx + inset, ry + inset
    xmax, ymax = rx + rw - inset, ry + rh - inset
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, x1 - xmin), (dx, xmax - x1),
                   (-dy, y1 - ymin), (dy, ymax - y1)):
        if abs(pp) < 1e-9:
            if qq < 0:
                return False
        else:
            t = qq / pp
            if pp < 0:
                if t > t1:
                    return False
                t0 = max(t0, t)
            else:
                if t < t0:
                    return False
                t1 = min(t1, t)
    return t0 <= t1


def band_seg_hit(x1, y1, x2, y2, p, q):
    """Пересекаются ли отрезки (x1,y1)-(x2,y2) и p-q."""
    def cross(ax, ay, bx, by, cx, cy):
        return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    d1 = cross(x1, y1, x2, y2, p[0], p[1])
    d2 = cross(x1, y1, x2, y2, q[0], q[1])
    d3 = cross(p[0], p[1], q[0], q[1], x1, y1)
    d4 = cross(p[0], p[1], q[0], q[1], x2, y2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def run_qa(name):
    problems = []
    for (sname, path) in QA_SEGS:
        for i in range(len(path) - 1):
            p0, p1 = path[i], path[i + 1]
            for (bkey, bx, by, bw, bh) in QA_BOXES:
                if seg_rect_hit(p0, p1, bx, by, bw, bh):
                    problems.append(
                        "линия «%s» проходит через плашку %s [(%.0f,%.0f)→(%.0f,%.0f)]"
                        % (sname, bkey, p0[0], p0[1], p1[0], p1[1]))
    for (txt, cx, cy, w, h) in QA_LABELS:
        bx1, by1, bx2, by2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        for (bkey, rx, ry, rw, rh) in QA_BOXES:
            if (bx1 < rx + rw - 3 and bx2 > rx + 3
                    and by1 < ry + rh - 3 and by2 > ry + 3):
                problems.append("подпись «%s» [(%.0f,%.0f)-(%.0f,%.0f)] "
                                "попадает на плашку %s" % (txt, bx1, by1, bx2, by2,
                                                           bkey))
        # текст не должен пересекаться с чужими линиями
        for (sname, path) in QA_SEGS:
            for i in range(len(path) - 1):
                if band_seg_hit(bx1, cy - 17, bx2, cy - 17, path[i], path[i + 1]) \
                        or band_seg_hit(bx1, cy - 2, bx2, cy - 2,
                                        path[i], path[i + 1]):
                    problems.append("подпись «%s» [(%.0f,%.0f)-(%.0f,%.0f)] "
                                    "перечёркнута линией «%s»"
                                    % (txt, bx1, cy - 17, bx2, cy - 2, sname))
    problems += QA_WARNS
    if problems:
        print("[QA] %s: НАЙДЕНО %d" % (name, len(problems)))
        for p in sorted(set(problems)):
            print("      -", p)
    else:
        print("[QA] %s: OK — %d связей, линии не пересекают плашки, "
              "подписи чистые" % (name, len(QA_SEGS)))
    return problems


def qa_reset():
    del QA_BOXES[:]
    del QA_SEGS[:]
    del QA_LABELS[:]
    del QA_WARNS[:]


# ---------------------------------------------------------------------------
# Легенда и сноски
# ---------------------------------------------------------------------------
def legend(s, y, items, right=30, gap=26):
    """items: [(подпись, палитра)] — цветные чипы в строку, выровнены вправо."""
    total = sum(44 + text_w(label, FS_LEG) for (label, _) in items) \
        + gap * (len(items) - 1)
    cx = s.w - right - total
    for (label, pal) in items:
        fill, stroke = pal
        s.rect(cx, y - 19, 34, 26, fill=fill, stroke=stroke, sw=2, rx=5)
        s.text(cx + 44, y, label, size=FS_LEG, anchor="start")
        cx += 44 + text_w(label, FS_LEG) + gap
    return cx


def footnote(s, x, y, text, max_w=1640, size=FS_NOTE, lead=34):
    lines = wrap(text, size, max_w)
    for i, line in enumerate(lines):
        s.text(x, y + i * lead, line, size=size, anchor="start", fill=C_SUB)
        if x + text_w(line, size) > s.w - 10:
            QA_WARNS.append("строка сноски шире полотна: «%s…»" % line[:40])
    last = y + (len(lines) - 1) * lead
    if last > s.h - 14:
        QA_WARNS.append("сноска выходит за нижний край полотна "
                        "(последняя строка y=%d, высота %d)" % (last, s.h))
    return last


# ===========================================================================
# 09. НОТАЦИЯ СВЯЗЕЙ
# ===========================================================================
def d09_notation():
    qa_reset()
    s = Svg(1700, 950, "Нотация связей «вороньи лапки»")
    s.header("Нотация связей «вороньи лапки» (crow's foot)",
             "Как читать ER-диаграммы CampusRent: символы у концов линии связи")

    # --- карточки-пояснения символов ------------------------------------
    cards = [
        ("одна черта — «один»", "ровно один экземпляр", "one"),
        ("воронья лапка — N", "много экземпляров", "many"),
        ("один ко многим (1:N)", "основной тип связи в БД", "onetomany"),
        ("кружок — «0..N»", "связь может отсутствовать", "opt"),
    ]
    cy = 175
    for i, (line1, line2, kind) in enumerate(cards):
        cxx = 30 + i * 415
        s.rect(cxx, 120, 395, 182, fill="#f9fafb", stroke=C_SOFT, sw=2, rx=10)
        ex, ey, ew, eh = cxx + 245, cy - 30, 120, 60
        s.rect(ex, ey, ew, eh, fill="#ffffff", stroke=C_GRAY, sw=2, rx=8)
        s.text(ex + ew / 2, ey + 40, "…", size=FS_TXT, fill=C_GRAY)
        s.line(cxx + 35, cy, ex, cy, stroke=C_LINE, sw=SW_LINE)
        if kind == "one":
            sym_one(s, ex, cy, -1, 0)
            card(s, "1", ex - BAR_D, cy - 30)
        elif kind == "many":
            sym_many(s, ex, cy, -1, 0)
            card(s, "N", ex - CF_APEX - 14, cy - 36)
        elif kind == "onetomany":
            sym_one(s, cxx + 35, cy, 1, 0)
            sym_many(s, ex, cy, -1, 0)
            card(s, "1", cxx + 35 + BAR_D, cy - 30)
            card(s, "N", ex - CF_APEX - 14, cy - 36)
        else:
            sym_circle(s, ex, cy, -1, 0, rmul=1.45)
            sym_many(s, ex, cy, -1, 0)
            card(s, "0..N", ex - 95, cy - 30)
        s.text(cxx + 20, 245, line1, size=FS_LEG, anchor="start", weight="bold")
        s.text(cxx + 20, 277, line2, size=FS_EN, anchor="start", fill=C_SUB)
        if text_w(line1, FS_LEG, "bold") + 40 > 395:
            QA_WARNS.append("карточка «%s»: текст шире плашки" % line1)
        if text_w(line2, FS_EN) + 40 > 395:
            QA_WARNS.append("карточка «%s»: пояснение шире плашки" % line1)

    # --- три примера ----------------------------------------------------
    panels = [
        (310, "Пример 1. Один к одному (1:1): «Заявка» — «Договор»",
         "У одной заявки не более одного договора; каждый договор относится ровно "
         "к одной заявке (со стороны заявки связь необязательна: 0..1).",
         [("Заявка", "requests", 110, 200, P_REQ),
          ("Договор", "contracts", 1290, 220, P_CTR)]),
        (520, "Пример 2. Один ко многим (1:N): «Модель» — «Экземпляр техники»",
         "Одной модели соответствует много экземпляров техники; каждый экземпляр "
         "принадлежит ровно одной модели.",
         [("Модель", "models", 110, 200, P_NSI),
          ("Экземпляр техники", "equipment_units", 1200, 360, P_EQ)]),
        (730, "Пример 3. Многие ко многим (M:N) через промежуточную таблицу",
         "Заявка содержит много позиций, каждая позиция ссылается на одну модель: "
         "M:N реализуется таблицей request_items.",
         [("Заявка", "requests", 90, 200, P_REQ),
          ("Позиция заявки", "request_items", 680, 300, P_REQ),
          ("Модель", "models", 1330, 200, P_NSI)]),
    ]
    for (py, cap, expl, boxes) in panels:
        s.rect(30, py, 1640, 198, fill="#ffffff", stroke=C_SOFT, sw=2, rx=12)
        s.text(60, py + 34, cap, size=FS_LEG, anchor="start", weight="bold",
               fill=C_LINE)
        if text_w(cap, FS_LEG, "bold") + 70 > 1640:
            QA_WARNS.append("заголовок панели шире рамки: «%s»" % cap)
        byy = py + 62
        for (ru, en, bx, bw, pal) in boxes:
            draw_ent(s, bx, byy, bw, 64, ru, en, pal, QA_BOXES, ru)
        mid = byy + 32
        if len(boxes) == 2:
            (ru1, en1, bx1, bw1, _), (ru2, en2, bx2, bw2, _) = boxes
            x1, x2 = bx1 + bw1, bx2
            s.line(x1, mid, x2, mid, stroke=C_LINE, sw=SW_LINE)
            QA_SEGS.append((cap, [(x1, mid), (x2, mid)]))
            sym_one(s, x1, mid, 1, 0)
            card(s, "1", x1 + BAR_D, mid - 30)
            if py == 310:                       # 1:1 — черта с двух сторон
                sym_one(s, x2, mid, -1, 0)
                card(s, "1", x2 - BAR_D, mid - 30)
            else:                               # 1:N
                sym_many(s, x2, mid, -1, 0)
                card(s, "N", x2 - CF_APEX - 16, mid - 36)
        else:
            (ru1, en1, bx1, bw1, _), (ru2, en2, bx2, bw2, _), \
                (ru3, en3, bx3, bw3, _) = boxes
            s.line(bx1 + bw1, mid, bx2, mid, stroke=C_LINE, sw=SW_LINE)
            QA_SEGS.append((cap + " (1)", [(bx1 + bw1, mid), (bx2, mid)]))
            sym_one(s, bx1 + bw1, mid, 1, 0)
            sym_many(s, bx2, mid, -1, 0)
            card(s, "1", bx1 + bw1 + BAR_D, mid - 30)
            card(s, "N", bx2 - CF_APEX - 16, mid - 36)
            s.line(bx2 + bw2, mid, bx3, mid, stroke=C_LINE, sw=SW_LINE)
            QA_SEGS.append((cap + " (2)", [(bx2 + bw2, mid), (bx3, mid)]))
            sym_many(s, bx2 + bw2, mid, 1, 0)
            sym_one(s, bx3, mid, -1, 0)
            card(s, "N", bx2 + bw2 + CF_APEX + 16, mid - 36, "start")
            card(s, "1", bx3 - BAR_D, mid - 30)
        for (k, line) in enumerate(wrap(expl, FS_LEG, 1560)):
            s.text(60, py + 156 + k * 32, line, size=FS_LEG, anchor="start",
                   fill=C_SUB)

    s.save("09_er_notation.svg")
    return run_qa("09_er_notation")


# ===========================================================================
# 10. ПОДСИСТЕМА «НСИ, КЛИЕНТЫ, ПЕРСОНАЛ»
# ===========================================================================
def d10_clients():
    qa_reset()
    s = Svg(CANVAS_W, CANVAS_H, "ER-диаграмма: НСИ, клиенты, персонал")
    s.header("ER-диаграмма: НСИ, клиенты, персонал",
             "10 таблиц подсистемы. Показаны ключевые поля: PK — первичный ключ, "
             "FK — внешний ключ; «…» — остальные поля")
    legend(s, 52, [("НСИ", P_NSI), ("персонал", P_HQ), ("клиенты", P_CLI)])

    tb = {}
    tb["categories"] = make_table("categories", "Категории", "categories", 0, 0, P_NSI, [
        ("PK", "CAT_ID"), ("", "CAT_NAME"), ("", "CAT_DESCR")])
    tb["models"] = make_table("models", "Модели", "models", 1, 0, P_NSI, [
        ("PK", "MOD_ID"), ("FK", "MOD_CAT"), ("", "MOD_BRAND"), ("", "MOD_NAME"),
        elide(2)])
    tb["tariffs"] = make_table("tariffs", "Тарифы", "tariffs", 2, 0, P_NSI, [
        ("PK", "TAR_ID"), ("FK", "TAR_MOD"), ("", "TAR_UNIT"), ("", "TAR_PRICE"),
        elide(2)])
    tb["model_components"] = make_table(
        "model_components", "Комплектация", "model_components", 0, 1, P_NSI, [
            ("PK", "MC_ID"), ("FK", "MC_MOD"), ("", "MC_ITEM"), ("", "MC_QTY")])
    tb["model_purposes"] = make_table(
        "model_purposes", "Назначения", "model_purposes", 1, 1, P_NSI, [
            ("PK", "MP_ID"), ("FK", "MP_MOD"), ("", "MP_PURPOSE")])
    tb["branches"] = make_table("branches", "Филиалы", "branches", 0, 2, P_HQ, [
        ("PK", "BR_ID"), ("", "BR_NAME"), ("", "BR_CITY"), ("", "BR_ADDRESS"),
        elide(2)])
    tb["employees"] = make_table("employees", "Сотрудники", "employees", 1, 2, P_HQ, [
        ("PK", "EMP_ID"), ("FK", "EMP_BR"), ("", "EMP_FIO"), ("", "EMP_POSITION"),
        ("", "EMP_LOGIN")])
    tb["universities"] = make_table(
        "universities", "ВУЗы", "universities", 0, 3, P_CLI, [
            ("PK", "UN_ID"), ("", "UN_SHORT"), ("", "UN_INN"), ("", "UN_CITY"),
            ("FK", "UN_BR")])
    tb["departments"] = make_table(
        "departments", "Подразделения", "departments", 1, 3, P_CLI, [
            ("PK", "DEP_ID"), ("FK", "DEP_UN"), ("", "DEP_NAME"), ("", "DEP_HEAD")])
    tb["representatives"] = make_table(
        "representatives", "Представители", "representatives", 2, 3, P_CLI, [
            ("PK", "REP_ID"), ("FK", "REP_UN"), ("FK", "REP_DEP"), ("", "REP_FIO"),
            elide(2)])

    bottom = place_tables(tb)

    # ---- связи ---------------------------------------------------------
    # categories 1 : N models
    edge(s, "categories→models",
         [B(tb["categories"], 205), T(tb["models"], 205)],
         labels=[("1", 185, 428, "end"), ("N", 226, 424, "start")])

    # models 1 : N model_components
    edge(s, "models→model_components",
         [R(tb["models"], 600), (420, 600), (420, 300),
          L(tb["model_components"], 300)],
         labels=[("1", 400, 576, "end"), ("N", 428, 272, "start")])

    # models 1 : N model_purposes (коридор ниже линии models→model_components)
    edge(s, "models→model_purposes",
         [R(tb["models"], 640), L(tb["model_purposes"], 640)],
         labels=[("1", 403, 608), ("N", 437, 606)])

    # models 1 : N tariffs
    edge(s, "models→tariffs",
         [B(tb["models"], 205), T(tb["tariffs"], 205)],
         labels=[("1", 185, 766, "end"), ("N", 226, 762, "start")])

    # branches 1 : N employees
    edge(s, "branches→employees",
         [B(tb["branches"], 1065), T(tb["employees"], 1065)],
         labels=[("1", 1045, 428, "end"), ("N", 1086, 424, "start")])

    # branches 1 : N universities
    edge(s, "branches→universities",
         [R(tb["branches"], 300), L(tb["universities"], 300)],
         labels=[("1", 1263, 268), ("N", 1296, 266)])

    # universities 1 : N departments
    edge(s, "universities→departments",
         [B(tb["universities"], 1495), T(tb["departments"], 1495)],
         labels=[("1", 1475, 428, "end"), ("N", 1516, 424, "start")])

    # departments 1 : N representatives
    edge(s, "departments→representatives",
         [B(tb["departments"], 1495), T(tb["representatives"], 1495)],
         labels=[("1", 1475, 766, "end"), ("N", 1516, 762, "start")])

    # universities 1 : N representatives — REP_DEP необязателен (пунктир)
    edge(s, "universities→representatives",
         [L(tb["universities"], 220), (1280, 220), (1280, 950),
          L(tb["representatives"], 950)],
         dash=True,
         labels=[("1", 1300, 196, "start"), ("N", 1310, 922, "end")])

    for t in tb.values():
        draw_table(s, t, QA_BOXES, QA_WARNS)

    footnote(s, 29, bottom + 34,
             "1 — «один», вороньи лапки — «многие»; пунктир — необязательная связь. "
             "На таблицы этой подсистемы ссылаются таблицы диаграммы 11: requests, "
             "request_items, equipment_units, transfers, rentals.")

    s.save("10_er_crowsfoot_clients.svg")
    return run_qa("10_er_crowsfoot_clients")


# ===========================================================================
# 11. ПОДСИСТЕМА «ТЕХНИКА, АРЕНДА, СЕРВИС»
# ===========================================================================
def d11_rental():
    qa_reset()
    s = Svg(CANVAS_W, CANVAS_H, "ER-диаграмма: техника, аренда, сервис")
    s.header("ER-диаграмма: техника, аренда, сервис",
             "12 таблиц подсистемы (4 справочника). Показаны ключевые поля: PK, FK; "
             "«…» — остальные поля")
    legend(s, 52, [("НСИ", P_NSI), ("техника", P_EQ), ("аренда", P_REQ),
                   ("договоры", P_CTR)])

    tb = {}
    tb["requests"] = make_table("requests", "Заявки", "requests", 0, 0, P_REQ, [
        ("PK", "REQ_ID"), ("FKX", "REQ_UN"), ("FKX", "REQ_DEP"),
        ("FKX", "REQ_REP"), ("FKX", "REQ_BR"), ("FK", "REQ_STATUS"), elide(3)])
    tb["request_items"] = make_table(
        "request_items", "Позиции заявки", "request_items", 1, 0, P_REQ, [
            ("PK", "RIT_ID"), ("FK", "RIT_REQ"), ("FKX", "RIT_MOD"),
            ("FKX", "RIT_TAR"), ("", "RIT_QTY"), elide(1)])
    tb["request_statuses"] = make_table(
        "request_statuses", "Статусы заявок", "request_statuses", 2, 0, P_NSI, [
            ("PK", "RST_ID"), ("", "RST_NAME")])
    tb["contracts"] = make_table("contracts", "Договоры", "contracts", 0, 1, P_CTR, [
        ("PK", "CTR_ID"), ("FK", "CTR_REQ"), ("", "CTR_NUMBER"), ("", "CTR_SUM"),
        ("", "CTR_STATUS"), elide(2)])
    tb["equipment_units"] = make_table(
        "equipment_units", "Экземпляры", "equipment_units", 1, 1, P_EQ, [
            ("PK", "EQ_ID"), ("FKX", "EQ_MOD"), ("FKX", "EQ_BR"),
            ("FK", "EQ_COND"), ("", "EQ_INV"), ("", "EQ_STATUS")])
    tb["condition_grades"] = make_table(
        "condition_grades", "Состояние", "condition_grades", 2, 1, P_NSI, [
            ("PK", "CG_ID"), ("", "CG_NAME")])
    tb["rentals"] = make_table("rentals", "Выдачи", "rentals", 0, 2, P_CTR, [
        ("PK", "RNT_ID"), ("FK", "RNT_CTR"), ("FK", "RNT_EQ"),
        ("FK", "RNT_COND_OUT"), ("FK", "RNT_COND_IN"), ("FKX", "RNT_EMP"),
        elide(3)])
    tb["transfers"] = make_table("transfers", "Перемещения", "transfers", 1, 2, P_EQ, [
        ("PK", "TR_ID"), ("FK", "TR_EQ"), ("FKX", "TR_FROM"), ("FKX", "TR_TO"),
        ("", "TR_DATE"), elide(1)])
    tb["maintenance_types"] = make_table(
        "maintenance_types", "Виды работ", "maintenance_types", 2, 2, P_NSI, [
            ("PK", "MT_ID"), ("", "MT_NAME")])
    tb["payments"] = make_table("payments", "Платежи", "payments", 0, 3, P_CTR, [
        ("PK", "PAY_ID"), ("FK", "PAY_CTR"), ("FK", "PAY_METHOD"), ("", "PAY_AMOUNT"),
        ("", "PAY_DATE"), elide(1)])
    tb["maintenance"] = make_table("maintenance", "Обслуживание", "maintenance",
                                   1, 3, P_CTR, [
        ("PK", "MNT_ID"), ("FK", "MNT_EQ"), ("FK", "MNT_TYPE"), ("", "MNT_BEGIN"),
        ("", "MNT_END"), ("", "MNT_COST")])
    tb["payment_methods"] = make_table(
        "payment_methods", "Способы оплаты", "payment_methods", 2, 3, P_NSI, [
            ("PK", "PM_ID"), ("", "PM_NAME")])

    bottom = place_tables(tb)

    # ---- связи ---------------------------------------------------------
    # request_statuses 1 : N requests — обход снизу: коридор слева от колонки 1,
    # затем по межрядному коридору в нижнюю грань requests
    edge(s, "request_statuses→requests",
         [R(tb["request_statuses"], 1000), (420, 1000), (420, 506), (300, 506),
          B(tb["requests"], 300)],
         labels=[("1", 426, 966, "start"), ("N", 326, 500, "start")])

    # requests 1 : N request_items
    edge(s, "requests→request_items",
         [B(tb["requests"], 205), T(tb["request_items"], 205)],
         labels=[("1", 185, 500, "end"), ("N", 230, 496, "start")])

    # requests 1 : 0..1 contracts (CTR_REQ — уникальный внешний ключ)
    edge(s, "requests→contracts",
         [R(tb["requests"], 300), L(tb["contracts"], 300)],
         many=False,
         labels=[("1", 403, 268), ("0..1", 420, 330)])

    # contracts 1 : N rentals
    edge(s, "contracts→rentals",
         [R(tb["contracts"], 300), L(tb["rentals"], 300)],
         labels=[("1", 833, 268), ("N", 866, 266)])

    # contracts 1 : N payments — нижний коридор (необязательная связь)
    edge(s, "contracts→payments",
         [B(tb["contracts"], 620), (620, 506), (1500, 506),
          B(tb["payments"], 1500)],
         dash=True,
         labels=[("1", 600, 490, "end"), ("N", 1526, 492, "start")])

    # equipment_units 1 : N rentals
    edge(s, "equipment_units→rentals",
         [R(tb["equipment_units"], 620), (822, 620), (822, 400),
          L(tb["rentals"], 400)],
         labels=[("1", 826, 648), ("N", 858, 366)])

    # equipment_units 1 : N transfers
    edge(s, "equipment_units→transfers",
         [R(tb["equipment_units"], 760), L(tb["transfers"], 760)],
         labels=[("1", 826, 730), ("N", 872, 726)])

    # equipment_units 1 : N maintenance — нижний коридор (необязательная)
    edge(s, "equipment_units→maintenance",
         [B(tb["equipment_units"], 700), (700, 880), (1500, 880),
          B(tb["maintenance"], 1500)],
         dash=True,
         labels=[("1", 730, 876, "start"), ("N", 1524, 872, "start")])

    # maintenance_types 1 : N maintenance
    edge(s, "maintenance_types→maintenance",
         [R(tb["maintenance_types"], 1000), (1280, 1000), (1280, 700),
          L(tb["maintenance"], 700)],
         labels=[("1", 1256, 976, "start"), ("N", 1270, 690, "end")])

    # condition_grades 1 : N equipment_units
    edge(s, "condition_grades→equipment_units",
         [T(tb["condition_grades"], 560), B(tb["equipment_units"], 560)],
         labels=[("1", 540, 890, "end"), ("N", 586, 886, "start")])

    # condition_grades 1 : N rentals (RNT_COND_OUT) — в нижнюю грань «Выдачи»
    edge(s, "condition_grades→rentals (RNT_COND_OUT)",
         [R(tb["condition_grades"], 990), (846, 990), (846, 520), (950, 520),
          B(tb["rentals"], 950)],
         labels=[("1", 820, 960, "start"), ("N", 980, 512, "start")])

    # condition_grades 1 : N rentals (RNT_COND_IN) — необязательная связь;
    # уводим её из правого коридора колонки 1 в левый, чтобы не сгущать подписи
    edge(s, "condition_grades→rentals (RNT_COND_IN)",
         [L(tb["condition_grades"], 1030), (400, 1030), (400, 534), (1120, 534),
          B(tb["rentals"], 1120)],
         dash=True,
         labels=[("1", 452, 1010, "end"), ("N", 1150, 512, "start")])

    # payment_methods 1 : N payments — правый коридор
    edge(s, "payment_methods→payments",
         [L(tb["payment_methods"], 1000), (1300, 1000), (1300, 300),
          L(tb["payments"], 300)],
         labels=[("1", 1265, 1030, "end"), ("N", 1282, 268, "end")])

    for t in tb.values():
        draw_table(s, t, QA_BOXES, QA_WARNS)

    footnote(s, 29, bottom + 34,
             "1 — «один», вороньи лапки — «многие», 0..1 — «один, но необязательно»; "
             "пунктир — необязательная связь. Серые поля с ↗ — внешние ключи к "
             "таблицам диаграммы 10.")

    s.save("11_er_crowsfoot_rental.svg")
    return run_qa("11_er_crowsfoot_rental")


# ===========================================================================
# Запуск
# ===========================================================================
def to_png(svg_name, width=CANVAS_W):
    if not shutil.which("rsvg-convert"):
        return None
    svg = os.path.join(OUT, svg_name)
    png = svg[:-4] + ".png"
    subprocess.run(["rsvg-convert", "-w", str(width), svg, "-o", png], check=True)
    return png


def main():
    os.makedirs(OUT, exist_ok=True)
    problems = []
    problems += d09_notation()
    problems += d10_clients()
    problems += d11_rental()
    for name in ("09_er_notation.svg", "10_er_crowsfoot_clients.svg",
                 "11_er_crowsfoot_rental.svg"):
        png = to_png(name)
        print("  %s -> %s" % (name, os.path.basename(png) if png else "PNG не создан"))
    print("Готово. QA:", "есть замечания" if problems else "замечаний нет")


if __name__ == "__main__":
    main()
