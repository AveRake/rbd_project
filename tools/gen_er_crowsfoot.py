#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — ER-диаграммы в нотации «вороньи лапки» (crow's foot) для презентации.

Создаёт файлы в каталоге diagrams/:
  09_er_notation.svg/.png           — нотация связей: 1:1, 1:N, M:N и как читать символы
  10_er_crowsfoot_clients.svg/.png  — подсистема «НСИ, клиенты, персонал» (10 таблиц)
  11_er_crowsfoot_rental.svg/.png   — подсистема «Техника, аренда, сервис» (12 таблиц)

Особенности реализации:
  * чистый Python + SVG, без внешних библиотек (тот же подход, что и в gen_diagrams.py);
  * полотно 1700 px по ширине, кегль текста не меньше 24 px, заголовки таблиц 27 px;
  * координаты плашек подобраны вручную; связи — ортогональные ломаные по свободным
    «коридорам» между плашками, поэтому линии не проходят сквозь таблицы;
  * встроенная проверка QA: каждый отрезок связи проверяется на пересечение с
    прямоугольниками таблиц, каждая подпись — на попадание в плашку и на чужие линии.

Запуск:  python3 tools/gen_er_crowsfoot.py
         (SVG пишутся всегда; PNG — через rsvg-convert -w 1700, если он есть в PATH)
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
# Геометрия
# ---------------------------------------------------------------------------
TBL_W = 330          # ширина плашки таблицы
HDR_H = 68           # высота шапки таблицы
LINE_H = 30          # шаг строки полей
PAD_TOP = 12
PAD_BOT = 10

BAR_D = 22           # расстояние от плашки до черты «один»
BAR_HH = 15          # половина длины черты «один»
CF_APEX = 26         # расстояние от плашки до вершины «вороньей лапки»
CF_SPREAD = 16       # половина раствора «вороньей лапки»
CIRC_D = 38          # расстояние от плашки до кружка «необязательно»
CIRC_R = 9

SW_LINE = 2.2
SW_SYM = 2.4
SW_BOX = 2.2

FS_TXT = 24          # основной кегль (минимум по заданию — 24)
FS_HDR = 27          # заголовок таблицы
FS_TITLE = 34
FS_RU_ENT = 27

# ---------------------------------------------------------------------------
# Оценка ширины строки (чистый Python, без библиотек) — контроль переполнения
# ---------------------------------------------------------------------------
_W_NARROW = set("iljI.,:;!|'`()[]{}-/\\ft ")
_W_WIDE = set("MW@ШЩЖЮФМmw")


def est_w(text, size):
    """Приблизительная ширина строки в пикселях (Helvetica, с запасом вверх)."""
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
        self.text(40, 54, title, size=FS_TITLE, anchor="start", weight="bold")
        if est_w(title, FS_TITLE) + 80 > self.w:
            QA_WARNS.append("заголовок шире полотна: «%s»" % title)
        if est_w(title, FS_TITLE) + 40 > 1010:
            QA_WARNS.append("заголовок доходит до легенды: «%s»" % title)
        if subtitle:
            self.text(40, 92, subtitle, size=FS_TXT, anchor="start", fill=C_SUB)
            if est_w(subtitle, FS_TXT) + 40 > 1010:
                QA_WARNS.append("подзаголовок доходит до легенды: «%s»" % subtitle)


def wrap(text, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if est_w(trial, size) <= max_w or not cur:
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


def tbl_h(n_fields):
    return HDR_H + PAD_TOP + n_fields * LINE_H + PAD_BOT


def L(t, y):
    return (t["x"], y)


def R(t, y):
    return (t["x"] + TBL_W, y)


def T(t, x):
    return (x, t["y"])


def B(t, x):
    return (x, t["y"] + t["h"])


def make_table(key, ru, en, x, y, pal, fields):
    return {"key": key, "ru": ru, "en": en, "x": x, "y": y, "pal": pal,
            "fields": fields, "h": tbl_h(len(fields))}


def draw_table(s, t, qa_boxes, qa_warns):
    x, y, w, h = t["x"], t["y"], TBL_W, t["h"]
    fill, stroke = t["pal"]
    s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=SW_BOX, rx=10)
    s.line(x, y + HDR_H, x + w, y + HDR_H, stroke=stroke, sw=2.0)
    s.text(x + 16, y + 33, t["ru"], size=FS_HDR, anchor="start", weight="bold",
           fill=stroke)
    s.text(x + 16, y + 60, t["en"], size=FS_TXT, anchor="start", fill=C_GRAY,
           italic=True)
    for i, (badge, name, typ) in enumerate(t["fields"]):
        by = y + HDR_H + PAD_TOP + i * LINE_H + 22
        if badge == "PK":
            s.text(x + 12, by, "PK", size=FS_TXT, anchor="start", weight="bold",
                   fill=C_LINE)
            s.text(x + 50, by, name, size=FS_TXT, anchor="start", weight="bold")
        elif badge == "FK":
            ext = name.endswith("↗")
            s.text(x + 12, by, "FK", size=FS_TXT, anchor="start", weight="bold",
                   fill=C_GRAY if ext else C_LINE)
            s.text(x + 50, by, name, size=FS_TXT, anchor="start",
                   fill=C_GRAY if ext else C_TXT)
        else:
            s.text(x + 50, by, name, size=FS_TXT, anchor="start")
        if typ:
            s.text(x + w - 10, by, typ, size=FS_TXT, anchor="end", fill=C_GRAY)
        used = 50 + est_w(name, FS_TXT) + (est_w(typ, FS_TXT) + 10 if typ else 0) + 10
        if used > w:
            qa_warns.append("%s: строка «%s %s» шире плашки (%.0f > %d)"
                            % (t["key"], name, typ, used, w))
    qa_boxes.append((t["key"], x, y, w, h))


def draw_ent(s, x, y, w, h, ru, en, pal, qa_boxes=None, key=None):
    """Плашка сущности для диаграммы нотации (без списка полей)."""
    fill, stroke = pal
    s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=SW_BOX, rx=10)
    s.text(x + w / 2, y + h / 2 - 4, ru, size=FS_RU_ENT, weight="bold", fill=stroke)
    s.text(x + w / 2, y + h / 2 + 24, en, size=FS_TXT, fill=C_GRAY, italic=True)
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
    s.text(x, y, txt, size=FS_TXT, anchor=anchor, weight="bold", fill=color)
    w = est_w(txt, FS_TXT)
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
                problems.append("подпись «%s» попадает на плашку %s" % (txt, bkey))
        # текст не должен пересекаться с чужими линиями
        for (sname, path) in QA_SEGS:
            for i in range(len(path) - 1):
                if band_seg_hit(bx1, cy - 17, bx2, cy - 17, path[i], path[i + 1]) \
                        or band_seg_hit(bx1, cy - 2, bx2, cy - 2,
                                        path[i], path[i + 1]):
                    problems.append("подпись «%s» перечёркнута линией «%s»"
                                    % (txt, sname))
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
def legend(s, x, y, items, qa_boxes=None):
    """items: [(подпись, палитра)] — цветные чипы в строку."""
    cx = x
    for (label, pal) in items:
        fill, stroke = pal
        s.rect(cx, y - 19, 34, 26, fill=fill, stroke=stroke, sw=2, rx=5)
        s.text(cx + 44, y, label, size=FS_TXT, anchor="start")
        cx += 44 + est_w(label, FS_TXT) + 34
    return cx


def footnote(s, x, y, text, max_w=1620):
    lines = wrap(text, FS_TXT, max_w)
    for i, line in enumerate(lines):
        s.text(x, y + i * 32, line, size=FS_TXT, anchor="start", fill=C_SUB)
    last = y + (len(lines) - 1) * 32
    if last > s.h - 14:
        QA_WARNS.append("сноска выходит за нижний край полотна "
                        "(последняя строка y=%d, высота %d)" % (last, s.h))
    for line in lines:
        if x + est_w(line, FS_TXT) > s.w - 10:
            QA_WARNS.append("строка сноски шире полотна: «%s…»" % line[:40])
    return last + 32


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
        ("воронья лапка — «многие»", "много экземпляров", "many"),
        ("один ко многим (1:N)", "основной тип связи в БД", "onetomany"),
        ("кружок — «необязательно»", "связь может отсутствовать (0..N)", "opt"),
    ]
    cy = 195
    for i, (line1, line2, kind) in enumerate(cards):
        cxx = 30 + i * 420
        s.rect(cxx, 130, 380, 150, fill="#f9fafb", stroke=C_SOFT, sw=2, rx=10)
        ex, ey, ew, eh = cxx + 240, cy - 30, 120, 60
        s.rect(ex, ey, ew, eh, fill="#ffffff", stroke=C_GRAY, sw=2, rx=8)
        s.text(ex + ew / 2, ey + 40, "…", size=FS_TXT, fill=C_GRAY)
        s.line(cxx + 40, cy, ex, cy, stroke=C_LINE, sw=SW_LINE)
        if kind == "one":
            sym_one(s, ex, cy, -1, 0)
            card(s, "1", ex - 34, cy - 18)
        elif kind == "many":
            sym_many(s, ex, cy, -1, 0)
            card(s, "N", ex - 44, cy - 18)
        elif kind == "onetomany":
            sym_one(s, cxx + 40, cy, 1, 0)
            sym_many(s, ex, cy, -1, 0)
            card(s, "1", cxx + 62, cy - 18)
            card(s, "N", ex - 44, cy - 18)
        else:
            sym_circle(s, ex, cy, -1, 0, rmul=1.45)
            sym_many(s, ex, cy, -1, 0)
            card(s, "0..N", ex - 92, cy - 18)
        s.text(cxx + 20, 240, line1, size=FS_TXT, anchor="start", weight="bold")
        s.text(cxx + 20, 268, line2, size=FS_TXT, anchor="start", fill=C_SUB)

    # --- три примера ----------------------------------------------------
    panels = [
        (300, "Пример 1. Один к одному (1:1): «Заявка» — «Договор»",
         "У одной заявки не более одного договора; каждый договор относится ровно "
         "к одной заявке (со стороны заявки связь необязательна: 0..1).",
         [("Заявка", "requests", 140, 300, P_REQ),
          ("Договор", "contracts", 1260, 300, P_CTR)]),
        (515, "Пример 2. Один ко многим (1:N): «Модель» — «Экземпляр техники»",
         "Одной модели соответствует много экземпляров техники; каждый экземпляр "
         "принадлежит ровно одной модели.",
         [("Модель", "models", 140, 300, P_NSI),
          ("Экземпляр техники", "equipment_units", 1180, 380, P_EQ)]),
        (730, "Пример 3. Многие ко многим (M:N) через промежуточную таблицу",
         "Заявка содержит много позиций, каждая позиция ссылается на одну модель: "
         "M:N реализуется таблицей request_items.",
         [("Заявка", "requests", 110, 260, P_REQ),
          ("Позиция заявки", "request_items", 700, 340, P_REQ),
          ("Модель", "models", 1310, 260, P_NSI)]),
    ]
    for (py, cap, expl, boxes) in panels:
        s.rect(30, py, 1640, 200, fill="#ffffff", stroke=C_SOFT, sw=2, rx=12)
        s.text(60, py + 38, cap, size=FS_TXT, anchor="start", weight="bold",
               fill=C_LINE)
        byy = py + 56
        for (ru, en, bx, bw, pal) in boxes:
            draw_ent(s, bx, byy, bw, 70, ru, en, pal, QA_BOXES, ru)
        mid = byy + 35
        if len(boxes) == 2:
            (ru1, en1, bx1, bw1, _), (ru2, en2, bx2, bw2, _) = boxes
            x1, x2 = bx1 + bw1, bx2
            s.line(x1, mid, x2, mid, stroke=C_LINE, sw=SW_LINE)
            QA_SEGS.append((cap, [(x1, mid), (x2, mid)]))
            sym_one(s, x1, mid, 1, 0)
            card(s, "1", x1 + 34, mid - 18)
            if py == 300:                       # 1:1 — черта с двух сторон
                sym_one(s, x2, mid, -1, 0)
                card(s, "1", x2 - 34, mid - 18)
            else:                               # 1:N
                sym_many(s, x2, mid, -1, 0)
                card(s, "N", x2 - 48, mid - 18)
        else:
            (ru1, en1, bx1, bw1, _), (ru2, en2, bx2, bw2, _), \
                (ru3, en3, bx3, bw3, _) = boxes
            s.line(bx1 + bw1, mid, bx2, mid, stroke=C_LINE, sw=SW_LINE)
            QA_SEGS.append((cap + " (1)", [(bx1 + bw1, mid), (bx2, mid)]))
            sym_one(s, bx1 + bw1, mid, 1, 0)
            sym_many(s, bx2, mid, -1, 0)
            card(s, "1", bx1 + bw1 + 34, mid - 18)
            card(s, "N", bx2 - 48, mid - 18)
            s.line(bx2 + bw2, mid, bx3, mid, stroke=C_LINE, sw=SW_LINE)
            QA_SEGS.append((cap + " (2)", [(bx2 + bw2, mid), (bx3, mid)]))
            sym_many(s, bx2 + bw2, mid, 1, 0)
            sym_one(s, bx3, mid, -1, 0)
            card(s, "N", bx2 + bw2 + 48, mid - 18)
            card(s, "1", bx3 - 34, mid - 18)
        for (k, line) in enumerate(wrap(expl, FS_TXT, 1560)):
            s.text(60, py + 160 + k * 30, line, size=FS_TXT, anchor="start",
                   fill=C_SUB)

    s.save("09_er_notation.svg")
    return run_qa("09_er_notation")


# ===========================================================================
# 10. ПОДСИСТЕМА «НСИ, КЛИЕНТЫ, ПЕРСОНАЛ»
# ===========================================================================
def d10_clients():
    qa_reset()
    s = Svg(1700, 1180, "ER-диаграмма: НСИ, клиенты, персонал")
    s.header("ER-диаграмма: НСИ, клиенты, персонал",
             "Подсистема из 10 таблиц; связи показаны в нотации «вороньи лапки»")
    legend(s, 1050, 46, [("НСИ", P_NSI), ("персонал", P_HQ),
                         ("клиенты", P_CLI)])

    tb = {}
    tb["categories"] = make_table("categories", "Категории", "categories",
                                  40, 130, P_NSI, [
        ("PK", "CAT_ID", "N(3)"), ("", "CAT_NAME", "V(60)"),
        ("", "CAT_DESCR", "V(200)")])
    tb["models"] = make_table("models", "Модели", "models", 40, 395, P_NSI, [
        ("PK", "MOD_ID", "N(6)"), ("FK", "MOD_CAT", "N(3)"),
        ("", "MOD_BRAND", "V(40)"), ("", "MOD_NAME", "V(80)"),
        ("", "MOD_COST", "N(12,2)"), ("", "MOD_MINQTY", "N(3)")])
    tb["model_components"] = make_table(
        "model_components", "Комплектация", "model_components", 470, 130, P_NSI, [
            ("PK", "MC_ID", "BIGINT"), ("FK", "MC_MOD", "N(6)"),
            ("", "MC_ITEM", "V(80)"), ("", "MC_QTY", "N(3)")])
    tb["model_purposes"] = make_table(
        "model_purposes", "Назначения", "model_purposes", 470, 425, P_NSI, [
            ("PK", "MP_ID", "BIGINT"), ("FK", "MP_MOD", "N(6)"),
            ("", "MP_PURPOSE", "V(60)")])
    tb["tariffs"] = make_table("tariffs", "Тарифы", "tariffs", 470, 690, P_NSI, [
        ("PK", "TAR_ID", "N(6)"), ("FK", "TAR_MOD", "N(6)"),
        ("", "TAR_UNIT", "V(10)"), ("", "TAR_PRICE", "N(10,2)"),
        ("", "TAR_BEGIN", "D"), ("", "TAR_END", "D")])
    tb["branches"] = make_table("branches", "Филиалы", "branches",
                                880, 130, P_HQ, [
        ("PK", "BR_ID", "V(8)"), ("", "BR_NAME", "V(100)"),
        ("", "BR_CITY", "V(50)"), ("", "BR_ADDRESS", "V(150)"),
        ("", "BR_MANAGER", "V(100)"), ("", "BR_BEGIN", "D")])
    tb["employees"] = make_table("employees", "Сотрудники", "employees",
                                 880, 475, P_HQ, [
        ("PK", "EMP_ID", "N(6)"), ("FK", "EMP_BR", "V(8)"),
        ("", "EMP_FIO", "V(100)"), ("", "EMP_POSITION", "V(60)"),
        ("", "EMP_LOGIN", "V(30)")])
    tb["universities"] = make_table("universities", "ВУЗы", "universities",
                                    1300, 130, P_CLI, [
        ("PK", "UN_ID", "N(6)"), ("", "UN_SHORT", "V(60)"),
        ("", "UN_INN", "C(10)"), ("", "UN_CITY", "V(50)"),
        ("FK", "UN_BR", "V(8)")])
    tb["departments"] = make_table("departments", "Подразделения", "departments",
                                   1300, 445, P_CLI, [
        ("PK", "DEP_ID", "N(6)"), ("FK", "DEP_UN", "N(6)"),
        ("", "DEP_NAME", "V(100)"), ("", "DEP_HEAD", "V(100)")])
    tb["representatives"] = make_table(
        "representatives", "Представители", "representatives", 1300, 740, P_CLI, [
            ("PK", "REP_ID", "N(6)"), ("FK", "REP_UN", "N(6)"),
            ("FK", "REP_DEP", "N(6)"), ("", "REP_FIO", "V(100)"),
            ("", "REP_POSITION", "V(60)"), ("", "REP_PHONE", "V(20)")])

    # ---- связи ---------------------------------------------------------
    # categories 1 : N models
    edge(s, "categories→models",
         [B(tb["categories"], 205), T(tb["models"], 205)],
         labels=[("1", 188, 342, "end"), ("N", 228, 386, "start")])

    # models 1 : N model_components
    edge(s, "models→model_components",
         [R(tb["models"], 520), (410, 520), (410, 240),
          L(tb["model_components"], 240)],
         labels=[("1", 392, 506), ("N", 444, 226)])

    # models 1 : N model_purposes
    edge(s, "models→model_purposes",
         [R(tb["models"], 550), (430, 550), (430, 520),
          L(tb["model_purposes"], 520)],
         labels=[("1", 400, 536), ("N", 446, 506)])

    # models 1 : N tariffs
    edge(s, "models→tariffs",
         [R(tb["models"], 580), (400, 580), (400, 780),
          L(tb["tariffs"], 780)],
         labels=[("1", 385, 566), ("N", 428, 764)])

    # branches 1 : N employees
    edge(s, "branches→employees",
         [B(tb["branches"], 1045), T(tb["employees"], 1045)],
         labels=[("1", 1028, 418, "end"), ("N", 1062, 460, "start")])

    # branches 1 : N universities
    edge(s, "branches→universities",
         [R(tb["branches"], 265), L(tb["universities"], 265)],
         labels=[("1", 1240, 251), ("N", 1284, 251)])

    # universities 1 : N departments
    edge(s, "universities→departments",
         [B(tb["universities"], 1465), T(tb["departments"], 1465)],
         labels=[("1", 1448, 390, "end"), ("N", 1484, 432, "start")])

    # departments 1 : N representatives
    edge(s, "departments→representatives",
         [B(tb["departments"], 1465), T(tb["representatives"], 1465)],
         labels=[("1", 1448, 686, "end"), ("N", 1484, 727, "start")])

    # universities 1 : N representatives — REP_DEP необязателен (пунктир)
    edge(s, "universities→representatives",
         [R(tb["universities"], 285), (1665, 285), (1665, 925),
          R(tb["representatives"], 925)],
         dash=True,
         labels=[("1", 1642, 271, "start"), ("N", 1640, 898, "start")])

    for t in tb.values():
        draw_table(s, t, QA_BOXES, QA_WARNS)

    footnote(s, 40, 1090,
             "Цвет: синий — НСИ (справочники), индиго — филиалы и персонал, "
             "зелёный — клиенты вузов. 1 — «один», вороньи лапки — «многие»; "
             "пунктир — необязательная связь. На таблицы подсистемы ссылаются "
             "таблицы диаграммы 11: requests (REQ_UN, REQ_DEP, REQ_REP, REQ_BR), "
             "equipment_units (EQ_MOD, EQ_BR), transfers (TR_FROM, TR_TO), "
             "rentals (RNT_EMP), request_items (RIT_MOD, RIT_TAR).", max_w=1620)

    s.save("10_er_crowsfoot_clients.svg")
    return run_qa("10_er_crowsfoot_clients")


# ===========================================================================
# 11. ПОДСИСТЕМА «ТЕХНИКА, АРЕНДА, СЕРВИС»
# ===========================================================================
def d11_rental():
    qa_reset()
    s = Svg(1700, 1250, "ER-диаграмма: техника, аренда, сервис")
    s.header("ER-диаграмма: техника, аренда, сервис",
             "Подсистема из 12 таблиц (4 справочника); связи в нотации «вороньи лапки»")
    legend(s, 1050, 46, [("НСИ", P_NSI), ("техника", P_EQ), ("аренда", P_REQ),
                         ("договоры", P_CTR)])

    tb = {}
    tb["requests"] = make_table("requests", "Заявки", "requests", 40, 130, P_REQ, [
        ("PK", "REQ_ID", "N(10)"), ("", "REQ_NUMBER", "C(12)"),
        ("FK", "REQ_UN", "↗"), ("FK", "REQ_DEP", "↗"), ("FK", "REQ_REP", "↗"),
        ("FK", "REQ_BR", "↗"), ("FK", "REQ_STATUS", "N(2)"),
        ("", "REQ_BEGIN", "D"), ("", "REQ_END", "D")])
    tb["request_items"] = make_table(
        "request_items", "Позиции заявки", "request_items", 40, 600, P_REQ, [
            ("PK", "RIT_ID", "N(10)"), ("FK", "RIT_REQ", "N(10)"),
            ("FK", "RIT_MOD", "↗"), ("FK", "RIT_TAR", "↗"),
            ("", "RIT_QTY", "N(3)"), ("", "RIT_COST", "N(12,2)")])
    tb["request_statuses"] = make_table(
        "request_statuses", "Статусы заявок", "request_statuses", 40, 940, P_NSI, [
            ("PK", "RST_ID", "N(2)"), ("", "RST_NAME", "V(30)")])
    tb["contracts"] = make_table("contracts", "Договоры", "contracts",
                                 470, 130, P_CTR, [
        ("PK", "CTR_ID", "N(10)"), ("", "CTR_NUMBER", "C(15)"),
        ("FK", "CTR_REQ", "N(10)"), ("", "CTR_BEGIN", "D"),
        ("", "CTR_END", "D"), ("", "CTR_SUM", "N(12,2)"),
        ("", "CTR_STATUS", "V(12)")])
    tb["equipment_units"] = make_table(
        "equipment_units", "Экземпляры техники", "equipment_units", 470, 600, P_EQ, [
            ("PK", "EQ_ID", "N(10)"), ("", "EQ_INV", "C(12)"),
            ("FK", "EQ_MOD", "↗"), ("FK", "EQ_BR", "↗"),
            ("FK", "EQ_COND", "N(2)"), ("", "EQ_STATUS", "V(12)")])
    tb["condition_grades"] = make_table(
        "condition_grades", "Степени состояния", "condition_grades", 470, 940, P_NSI, [
            ("PK", "CG_ID", "N(2)"), ("", "CG_NAME", "V(30)")])
    tb["rentals"] = make_table("rentals", "Выдачи", "rentals", 880, 130, P_CTR, [
        ("PK", "RNT_ID", "N(10)"), ("FK", "RNT_CTR", "N(10)"),
        ("FK", "RNT_EQ", "N(10)"), ("", "RNT_ISSUE", "D"),
        ("", "RNT_DUE", "D"), ("", "RNT_RETURN", "D"),
        ("FK", "RNT_COND_OUT", "N(2)"), ("FK", "RNT_COND_IN", "N(2)"),
        ("FK", "RNT_EMP", "↗")])
    tb["transfers"] = make_table("transfers", "Перемещения", "transfers",
                                 880, 600, P_EQ, [
        ("PK", "TR_ID", "N(10)"), ("FK", "TR_EQ", "N(10)"),
        ("FK", "TR_FROM", "↗"), ("FK", "TR_TO", "↗"),
        ("", "TR_DATE", "D"), ("", "TR_REASON", "V(200)")])
    tb["maintenance"] = make_table("maintenance", "Обслуживание", "maintenance",
                                   1300, 600, P_CTR, [
        ("PK", "MNT_ID", "N(10)"), ("FK", "MNT_EQ", "N(10)"),
        ("FK", "MNT_TYPE", "N(2)"), ("", "MNT_BEGIN", "D"),
        ("", "MNT_END", "D"), ("", "MNT_COST", "N(10,2)")])
    tb["payments"] = make_table("payments", "Платежи", "payments", 1300, 130, P_CTR, [
        ("PK", "PAY_ID", "N(10)"), ("FK", "PAY_CTR", "N(10)"),
        ("FK", "PAY_METHOD", "N(2)"), ("", "PAY_DATE", "D"),
        ("", "PAY_AMOUNT", "N(12,2)"), ("", "PAY_PURPOSE", "V(100)")])
    tb["maintenance_types"] = make_table(
        "maintenance_types", "Виды обслуживания", "maintenance_types", 880, 940, P_NSI, [
            ("PK", "MT_ID", "N(2)"), ("", "MT_NAME", "V(40)")])
    tb["payment_methods"] = make_table(
        "payment_methods", "Способы оплаты", "payment_methods", 1300, 940, P_NSI, [
            ("PK", "PM_ID", "N(2)"), ("", "PM_NAME", "V(30)")])

    # ---- связи ---------------------------------------------------------
    # request_statuses 1 : N requests — обход слева
    edge(s, "request_statuses→requests",
         [L(tb["request_statuses"], 1025), (20, 1025), (20, 574), (150, 574),
          B(tb["requests"], 150)],
         labels=[("1", 34, 1058, "end"), ("N", 120, 562, "end")])

    # requests 1 : N request_items
    edge(s, "requests→request_items",
         [B(tb["requests"], 205), T(tb["request_items"], 205)],
         labels=[("1", 188, 512, "end"), ("N", 228, 584, "start")])

    # requests 1 : 0..1 contracts (CTR_REQ — уникальный внешний ключ)
    edge(s, "requests→contracts",
         [R(tb["requests"], 285), L(tb["contracts"], 285)],
         many=False,
         labels=[("1", 392, 271), ("0..1", 448, 271)])

    # contracts 1 : N rentals
    edge(s, "contracts→rentals",
         [R(tb["contracts"], 255), L(tb["rentals"], 255)],
         labels=[("1", 828, 241), ("N", 872, 241)])

    # contracts 1 : N payments — нижний коридор (необязательная связь)
    edge(s, "contracts→payments",
         [B(tb["contracts"], 620), (620, 574), (1450, 574),
          B(tb["payments"], 1450)],
         dash=True,
         labels=[("1", 636, 560, "start"), ("N", 1418, 562, "end")])

    # payment_methods 1 : N payments — правый коридор
    edge(s, "payment_methods→payments",
         [R(tb["payment_methods"], 1025), (1665, 1025), (1665, 522),
          (1580, 522), B(tb["payments"], 1580)],
         labels=[("1", 1642, 1011, "start"), ("N", 1572, 510, "end")])

    # equipment_units 1 : N rentals
    edge(s, "equipment_units→rentals",
         [R(tb["equipment_units"], 715), (850, 715), (850, 440),
          L(tb["rentals"], 440)],
         labels=[("1", 828, 701), ("N", 866, 426, "end")])

    # equipment_units 1 : N transfers
    edge(s, "equipment_units→transfers",
         [R(tb["equipment_units"], 745), L(tb["transfers"], 745)],
         labels=[("1", 828, 731), ("N", 872, 731)])

    # equipment_units 1 : N maintenance — нижний коридор (необязательная)
    edge(s, "equipment_units→maintenance",
         [B(tb["equipment_units"], 700), (700, 908), (1560, 908),
          B(tb["maintenance"], 1560)],
         dash=True,
         labels=[("1", 716, 930, "start"), ("N", 1530, 890, "end")])

    # maintenance_types 1 : N maintenance
    edge(s, "maintenance_types→maintenance",
         [R(tb["maintenance_types"], 1025), (1255, 1025), (1255, 930),
          (1400, 930), B(tb["maintenance"], 1400)],
         labels=[("1", 1232, 1011, "start"), ("N", 1385, 890, "end")])

    # condition_grades 1 : N equipment_units
    edge(s, "condition_grades→equipment_units",
         [T(tb["condition_grades"], 600), B(tb["equipment_units"], 600)],
         labels=[("1", 570, 916, "end"), ("N", 570, 890, "end")])

    # condition_grades 1 : N rentals (RNT_COND_OUT) — через левый коридор
    y0 = fy(tb["condition_grades"], 0)
    edge(s, "condition_grades→rentals (RNT_COND_OUT)",
         [L(tb["condition_grades"], y0), (412, y0), (412, 522), (1060, 522),
          B(tb["rentals"], 1060)],
         labels=[("1", 392, y0 - 14, "end"), ("N", 1028, 508, "end")])

    # condition_grades 1 : N rentals (RNT_COND_IN) — необязательная связь
    y1 = fy(tb["condition_grades"], 1)
    edge(s, "condition_grades→rentals (RNT_COND_IN)",
         [L(tb["condition_grades"], y1), (428, y1), (428, 548), (1180, 548),
          B(tb["rentals"], 1180)],
         dash=True,
         labels=[("1", 408, y1 + 26, "end"), ("N", 1148, 536, "end")])

    for t in tb.values():
        draw_table(s, t, QA_BOXES, QA_WARNS)

    footnote(s, 40, 1128,
             "Цвет: синий — НСИ, жёлтый — техника, красный — заявки и аренда, "
             "оранжевый — договоры и сервис. 1 — «один», вороньи лапки — «многие», "
             "0..1 — «один, но необязательно»; пунктир — необязательная связь. "
             "Серые поля с ↗ — внешние ключи к таблицам диаграммы 10: requests "
             "(REQ_UN, REQ_DEP, REQ_REP, REQ_BR), request_items (RIT_MOD, RIT_TAR), "
             "equipment_units (EQ_MOD, EQ_BR), transfers (TR_FROM, TR_TO), "
             "rentals (RNT_EMP).", max_w=1620)

    s.save("11_er_crowsfoot_rental.svg")
    return run_qa("11_er_crowsfoot_rental")


# ===========================================================================
# Запуск
# ===========================================================================
def to_png(svg_name, width=1700):
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
