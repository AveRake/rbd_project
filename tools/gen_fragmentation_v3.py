#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — схема фрагментации РБД, версия 3: ДВА новых крупных варианта.

Файлы-результаты (старые diagrams/05b_fragmentation.* НЕ трогаются):

  diagrams/05c_fragmentation_cards.svg / .png   (1700 x 1000)
      ВАРИАНТ A — узло-центричная схема. Четыре крупные карточки узлов
      (ЦО, СПб, Казань, узел консолидации) в просторной сетке 2 x 2.
      Между карточками — широкие коридоры; в каждом коридоре у каждой
      стрелки СВОЙ ряд (не меньше 36 px между рядами), свой цвет
      (РОК — синий, РБОК — зелёный, РКД — оранжевый) и своя подпись.
      Двунаправленный РБОК между соседними карточками — ДВЕ параллельные
      стрелки с наконечниками в противоположные стороны ("бантиков" нет).
      Дальние пары РБОК (ЦО<->consol, СПб<->Казань) и РОК ЦО->consol
      разведены ортогональными трассами в перекрёстке коридоров.

  diagrams/05d_fragmentation_matrix.svg / .png  (1700 x 1000)
      ВАРИАНТ B — просторная матрица «6 групп данных x 4 узла»:
      зазор между ячейками 30 px по вертикали и 40-44 px по горизонтали,
      кегль 26 px (заголовки узлов 30 px). ВНУТРИ матрицы стрелок нет
      вообще. Под матрицей — широкая панель «Потоки данных» в 3 строки
      с тремя крупными значками-стрелками и пояснениями РОК / РБОК / РКД,
      ниже — легенда цветов групп.

Встроенная проверка вёрстки (см. Svg.check):
  * наложение прямоугольников (блоков) и зазор меньше MIN_BLOCK_GAP;
  * наложение текста на текст, выход текста за полотно и за отведённую
    ширину (maxw);
  * текст поверх линий;
  * линия внутри блока-карточки (трасса не должна идти по карточке);
  * наконечники: расстояние между наконечниками меньше MIN_HEAD_GAP,
    пересечение наконечников, наконечник внутри блока;
  * совпадающие (наложенные друг на друга) отрезки.

Панели-контейнеры (легенда, панель потоков) помечены container=True:
их собственные значки и подписи внутри разрешены, а вот зазор до других
блоков и наложения текста проверяются так же строго.

SVG генерируется чистым Python, PNG — командой
    rsvg-convert -w 1700 файл.svg -o файл.png

Запуск:  python3 tools/gen_fragmentation_v3.py [A|B]
"""

import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "diagrams")

FONT = "Helvetica, Arial, sans-serif"

# --------------------------------------------------------------------------
# Палитра — та же, что в tools/gen_diagrams.py и tools/gen_diagrams_v2.py
# --------------------------------------------------------------------------
C_LINE = "#1f2937"
C_REF_F, C_REF_S = "#dbeafe", "#1d4ed8"   # НСИ — синий
C_CLI_F, C_CLI_S = "#dcfce7", "#15803d"   # клиенты — зелёный
C_EQ_F, C_EQ_S = "#fef9c3", "#a16207"     # техника — жёлтый
C_REQ_F, C_REQ_S = "#fee2e2", "#b91c1c"   # заявки — красный
C_CTR_F, C_CTR_S = "#ffedd5", "#c2410c"   # договоры — оранжевый
C_SRV_F, C_SRV_S = "#ede9fe", "#6d28d9"   # обслуживание — фиолетовый
C_NEU_F, C_NEU_S = "#f3f4f6", "#4b5563"   # нейтральный
C_HQ_F, C_HQ_S = "#e0e7ff", "#3730a3"     # ЦО / персонал

# цвета методов поддержки (потоки данных)
C_ROK = "#1d4ed8"    # РОК  — синий
C_RBOK = "#15803d"   # РБОК — зелёный
C_RKD = "#c2410c"    # РКД  — оранжевый

MIN_SIZE = 26        # минимальный кегль
HEAD_SIZE = 30       # заголовки блоков
TITLE_SIZE = 34      # заголовок схемы

MIN_BLOCK_GAP = 30   # минимальный зазор между блоками, px
MIN_HEAD_GAP = 22    # минимальное расстояние между наконечниками, px
HEAD_LEN = 26        # длина наконечника, px
HEAD_HALF = 11       # полуширина наконечника, px


# ==========================================================================
# Измерение ширины строки тем же шрифтом, которым рисует rsvg-convert
# ==========================================================================
_FONT_CACHE = {}
_FONT_FILES = {
    False: ("/System/Library/Fonts/Helvetica.ttc", 0),
    True: ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
}
SAFETY = 1.02


def _font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        from PIL import ImageFont
        path, idx = _FONT_FILES[bold]
        _FONT_CACHE[key] = ImageFont.truetype(path, size, index=idx)
    return _FONT_CACHE[key]


def tw(text, size, bold=False):
    """Ширина строки в px (с запасом на метрики шрифта)."""
    return _font(size, bold).getlength(text) * SAFETY


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ==========================================================================
# Геометрические помощники (для автопроверки)
# ==========================================================================
def seg_rect_hit(x1, y1, x2, y2, rx0, ry0, rx1, ry1):
    """Пересекается ли отрезок с прямоугольником (Лианг—Барски)."""
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - rx0), (dx, rx1 - x1), (-dy, y1 - ry0), (dy, ry1 - y1)):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return False
                if r < t1:
                    t1 = r
    return True


def rect_gap(a, b):
    """Евклидово расстояние между двумя прямоугольниками (0 при наложении)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    dx = max(0.0, max(ax - (bx + bw), bx - (ax + aw)))
    dy = max(0.0, max(ay - (by + bh), by - (ay + ah)))
    return math.hypot(dx, dy)


def point_in_rect(px, py, r, inset=0.0):
    x, y, w, h = r
    return (x + inset) < px < (x + w - inset) and (y + inset) < py < (y + h - inset)


def poly_intersect(p1, p2):
    """Пересечение двух выпуклых многоугольников (теорема о разделяющей оси)."""
    for poly in (p1, p2):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            nx, ny = -(y2 - y1), (x2 - x1)
            a = [nx * px + ny * py for px, py in p1]
            b = [nx * px + ny * py for px, py in p2]
            if max(a) < min(b) - 1e-9 or max(b) < min(a) - 1e-9:
                return False
    return True


def head_poly(tip, ux, uy):
    """Многоугольник наконечника: tip — остриё, (ux,uy) — направление полёта."""
    bx, by = tip[0] - ux * HEAD_LEN, tip[1] - uy * HEAD_LEN
    nx, ny = -uy, ux
    return [tip, (bx + nx * HEAD_HALF, by + ny * HEAD_HALF),
            (bx - nx * HEAD_HALF, by - ny * HEAD_HALF)]


# ==========================================================================
# SVG-документ с автопроверкой вёрстки
# ==========================================================================
class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts = []
        self.head_parts = []
        self.blocks = []      # (x, y, w, h, name, container)
        self.decor = []       # (x, y, w, h, name)      — плашки-образцы цвета
        self.texts = []       # (x0, y0, x1, y1, text)
        self.segs = []        # (x1, y1, x2, y2, sw)
        self.heads = []       # (poly, tip, name)
        self.fit = []         # текст шире отведённого места
        self.min_gap = MIN_BLOCK_GAP

    # --- примитивы --------------------------------------------------------
    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=C_LINE, sw=2, rx=12,
             dash=None, kind=None, name="", container=False):
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
        if kind == "block":
            self.blocks.append((x, y, w, h, name, container))
        elif kind == "decor":
            self.decor.append((x, y, w, h, name))
        return (x, y, w, h)

    def text(self, x, y, s, size=MIN_SIZE, anchor="middle", weight="normal",
             fill="#111827", bold=None, maxw=None):
        if size < MIN_SIZE:
            raise ValueError(f"кегль {size} < {MIN_SIZE}: {s!r}")
        if bold is None:
            bold = (weight == "bold")
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" '
                 f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
                 f'fill="{fill}">{esc(s)}</text>')
        w = tw(s, size, bold)
        if maxw is not None and w > maxw:
            self.fit.append(f"текст шире места ({w:.0f} > {maxw:.0f}): {s!r}")
        asc, desc = _font(size, bold).getmetrics()
        if anchor == "start":
            x0 = x
        elif anchor == "end":
            x0 = x - w
        else:
            x0 = x - w / 2.0
        self.texts.append((x0, y - asc, x0 + w, y + desc, s))
        return w

    def line(self, x1, y1, x2, y2, stroke=C_LINE, sw=2.4, dash=None, record=False):
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"{d}/>')
        if record:
            self.segs.append((x1, y1, x2, y2, sw))

    def poly(self, pts, stroke=C_LINE, sw=2.4, dash=None):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<polyline points="{p}" fill="none" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linejoin="round" '
                 f'stroke-linecap="round"{d}/>')
        for i in range(len(pts) - 1):
            self.segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], sw))

    def head(self, tip, direction, color, name=""):
        """Наконечник стрелки отдельным многоугольником (точная геометрия)."""
        ux, uy = direction
        n = math.hypot(ux, uy) or 1.0
        ux, uy = ux / n, uy / n
        poly = head_poly(tip, ux, uy)
        pts = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in poly)
        self.head_parts.append(f'<polygon points="{pts}" fill="{color}"/>')
        self.heads.append((poly, tip, name))

    def arrow(self, pts, color, head_end=True, head_start=False, sw=2.4, name=""):
        """Ломаная со стрелочными наконечниками на концах."""
        if len(pts) < 2:
            raise ValueError("arrow: нужно >= 2 точек")
        self.poly(pts, stroke=color, sw=sw)
        if head_end:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            self.head((x2, y2), (x2 - x1, y2 - y1), color, name)
        if head_start:
            (x1, y1), (x2, y2) = pts[1], pts[0]
            self.head((x2, y2), (x2 - x1, y2 - y1), color, name + " (обратно)")
        return self

    # --- сборка файла -----------------------------------------------------
    def render(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="#ffffff"/>')
        body = "\n".join(self.parts) + "\n" + "\n".join(self.head_parts)
        return head + "\n" + body + "\n</svg>\n"

    # --- автопроверка -----------------------------------------------------
    def check(self):
        problems = list(self.fit)

        # 1. зазоры и наложения блоков
        for i in range(len(self.blocks)):
            for j in range(i + 1, len(self.blocks)):
                a, b = self.blocks[i], self.blocks[j]
                g = rect_gap(a[:4], b[:4])
                if g < self.min_gap:
                    problems.append(
                        f"зазор блоков {g:.1f} px < {self.min_gap}: "
                        f"{a[4]!r} <-> {b[4]!r}")

        # 2. текст: за полотном, наложения, ширина
        for (x0, y0, x1, y1, t) in self.texts:
            if x0 < 3 or y0 < 3 or x1 > self.w - 3 or y1 > self.h - 3:
                problems.append(
                    f"текст за полотном: {t!r} bbox=({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})")
        tb = self.texts
        for i in range(len(tb)):
            for j in range(i + 1, len(tb)):
                a, b = tb[i], tb[j]
                if (a[0] < b[2] - 2 and b[0] < a[2] - 2
                        and a[1] < b[3] - 2 and b[1] < a[3] - 2):
                    problems.append(f"наложение текста: {a[4]!r} <-> {b[4]!r}")

        # 3. текст поверх линий
        for (x0, y0, x1, y1, t) in tb:
            for (sx1, sy1, sx2, sy2, sw) in self.segs:
                if seg_rect_hit(sx1, sy1, sx2, sy2, x0 + 2, y0 + 2, x1 - 2, y1 - 2):
                    problems.append(
                        f"текст на линии: {t!r} линия ({sx1:.0f},{sy1:.0f})-"
                        f"({sx2:.0f},{sy2:.0f})")

        # 4. линия внутри блока-карточки (трасса не должна идти по карточке)
        for (sx1, sy1, sx2, sy2, sw) in self.segs:
            for (bx, by, bw, bh, name, container) in self.blocks:
                if container:
                    continue
                if seg_rect_hit(sx1, sy1, sx2, sy2, bx + 3, by + 3,
                                bx + bw - 3, by + bh - 3):
                    problems.append(
                        f"линия внутри блока {name!r}: ({sx1:.0f},{sy1:.0f})-"
                        f"({sx2:.0f},{sy2:.0f})")

        # 5. наконечники
        for i in range(len(self.heads)):
            pi, ti, ni = self.heads[i]
            for j in range(i + 1, len(self.heads)):
                pj, tj, nj = self.heads[j]
                d = math.dist(ti, tj)
                if poly_intersect(pi, pj):
                    problems.append(f"наконечники пересекаются: {ni!r} <-> {nj!r}")
                elif d < MIN_HEAD_GAP:
                    problems.append(
                        f"наконечники ближе {MIN_HEAD_GAP} px ({d:.0f}): "
                        f"{ni!r} <-> {nj!r} в ({ti[0]:.0f},{ti[1]:.0f})")
        for poly, tip, name in self.heads:
            for (bx, by, bw, bh, bname, container) in self.blocks:
                if container:
                    continue
                r = (bx, by, bw, bh)
                if any(point_in_rect(px, py, r, 0.5) for px, py in poly[1:]):
                    problems.append(
                        f"наконечник {name!r} упирается в блок {bname!r}")

        # 6. совпадающие отрезки (наложение линий друг на друга)
        for i in range(len(self.segs)):
            for j in range(i + 1, len(self.segs)):
                if self._seg_overlap(self.segs[i], self.segs[j]):
                    a, b = self.segs[i], self.segs[j]
                    problems.append(
                        f"наложение линий: ({a[0]:.0f},{a[1]:.0f})-({a[2]:.0f},{a[3]:.0f}) "
                        f"и ({b[0]:.0f},{b[1]:.0f})-({b[2]:.0f},{b[3]:.0f})")
        return problems

    @staticmethod
    def _seg_overlap(a, b, tol=3.0):
        """Коллинеарные отрезки, накладывающиеся более чем на tol px."""
        ax1, ay1, ax2, ay2 = a[0], a[1], a[2], a[3]
        bx1, by1, bx2, by2 = b[0], b[1], b[2], b[3]
        dx, dy = ax2 - ax1, ay2 - ay1
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        if (abs((bx1 - ax1) * nx + (by1 - ay1) * ny) > tol
                or abs((bx2 - ax1) * nx + (by2 - ay1) * ny) > tol):
            return False
        ux, uy = dx / ln, dy / ln
        b0 = (bx1 - ax1) * ux + (by1 - ay1) * uy
        b1 = (bx2 - ax1) * ux + (by2 - ay1) * uy
        lo, hi = min(b0, b1), max(b0, b1)
        return min(ln, hi) - max(0.0, lo) > tol


# ==========================================================================
# Общие куски оформления
# ==========================================================================
def title_block(s, title, subtitle):
    s.text(50, 56, title, size=TITLE_SIZE, weight="bold", anchor="start",
           maxw=1600)
    s.text(50, 94, subtitle, size=MIN_SIZE, fill="#4b5563", anchor="start",
           maxw=1600)


def flow_icon(s, x, y, color, two_way, ln=96):
    """Крупный значок-стрелка для легенды потоков."""
    s.arrow([(x, y), (x + ln, y)], color, head_end=True, head_start=two_way,
            sw=5.0, name=f"значок {color}")


def swatch(s, x, y, fill, stroke, name, size=18):
    s.rect(x, y, size, size, fill=fill, stroke=stroke, sw=2, rx=4,
           kind="decor", name=name)


# ==========================================================================
# ВАРИАНТ A — узло-центричная схема (1700 x 1000)
# ==========================================================================
def d05c_fragmentation_cards():
    s = Svg(1700, 1000, "Фрагментация: карточки узлов")
    title_block(
        s,
        "Схема фрагментации РБД «CampusRent»: узлы и потоки данных",
        "Вариант A: состав каждого узла и потоки данных между узлами; "
        "цвет стрелки — метод поддержки")

    # ---------------- карточки узлов (сетка 2 x 2) -----------------------
    CW, CH = 590, 290
    HQ = (50, 110, CW, CH)
    SPB = (1060, 110, CW, CH)
    KZN = (50, 560, CW, CH)
    CON = (1060, 560, CW, CH)
    # коридоры: между столбцами 640..1060 (420 px), между строками 400..560 (160 px)

    groups = [
        ("НСИ и справочники", C_REF_F, C_REF_S),
        ("Клиенты", C_CLI_F, C_CLI_S),
        ("Экземпляры техники", C_EQ_F, C_EQ_S),
        ("Заявки и позиции", C_REQ_F, C_REQ_S),
        ("Договоры и платежи", C_CTR_F, C_CTR_S),
        ("Обслуживание и ремонт", C_SRV_F, C_SRV_S),
    ]

    def card(r, name, city, accent_f, accent_s, bullets):
        x, y, w, h = r
        s.rect(x, y, w, h, fill="#ffffff", stroke=accent_s, sw=3, rx=16,
               kind="block", name=name)
        s.rect(x, y, w, 84, fill=accent_f, stroke=accent_f, sw=0, rx=16)
        s.rect(x, y + 64, w, 20, fill=accent_f, stroke=accent_f, sw=0, rx=0)
        s.text(x + 26, y + 44, name, size=32, weight="bold", anchor="start",
               fill=accent_s, maxw=w - 52)
        s.text(x + 26, y + 74, city, size=MIN_SIZE, anchor="start",
               fill="#374151", maxw=w - 52)
        s.line(x + 26, y + 96, x + w - 26, y + 96, stroke="#d1d5db", sw=1.5)
        for i, (gi, txt) in enumerate(bullets):
            yb = y + 128 + i * 31
            _, gf, gs = groups[gi]
            swatch(s, x + 26, yb - 18, gf, gs, f"плашка {name} #{gi}")
            s.text(x + 56, yb, txt, size=MIN_SIZE, anchor="start",
                   fill="#111827", maxw=w - 84)

    card(HQ, "Центральный офис", "HQ · Москва · мастер РОК, центр РКД",
         C_HQ_F, C_HQ_S, [
             (0, "НСИ — основная копия (мастер)"),
             (1, "Клиенты — реплика РБОК (РИ)"),
             (2, "Техника — консолидированная копия"),
             (3, "Заявки — согласование и учёт"),
             (4, "Договоры, платежи — основная копия"),
             (5, "Обслуживание — сводный учёт затрат"),
         ])
    card(SPB, "Филиал СПб", "Санкт-Петербург · узел SPB",
         C_NEU_F, C_NEU_S, [
             (0, "НСИ — реплика (снимок 1 раз/сут)"),
             (1, "Клиенты — реплика РБОК (РИ)"),
             (2, "Техника — фрагмент EQ_BR = СПб"),
             (3, "Заявки — рабочая копия + позиции"),
             (4, "Договоры, выдачи, платежи — локально"),
             (5, "Обслуживание и ремонт — локально"),
         ])
    card(KZN, "Филиал Казань", "Казань · узел KZN",
         C_NEU_F, C_NEU_S, [
             (0, "НСИ — реплика (снимок 1 раз/сут)"),
             (1, "Клиенты — реплика РБОК (РИ)"),
             (2, "Техника — фрагмент EQ_BR = KZN"),
             (3, "Заявки — рабочая копия + позиции"),
             (4, "Договоры, выдачи, платежи — локально"),
             (5, "Обслуживание и ремонт — локально"),
         ])
    card(CON, "Узел консолидации", "consol · витрина аналитики",
         C_CTR_F, C_CTR_S, [
             (0, "НСИ — реплика (снимок 1 раз/сут)"),
             (1, "Клиенты — реплика РБОК (РИ)"),
             (2, "Техника — консолидированная копия"),
             (3, "Заявки — консолидированная копия"),
             (4, "Договоры, платежи — сводные копии"),
             (5, "Обслуживание — сводный учёт затрат"),
         ])

    # ---------------- коридор «ЦО — СПб» (верхний) ------------------------
    def h_lane(y, color, head_right, label):
        if head_right:
            s.arrow([(640, y), (1060, y)], color, head_end=True,
                    name=f"наконечник {label}")
        else:
            s.arrow([(1060, y), (640, y)], color, head_end=True,
                    name=f"наконечник {label}")
        s.text(850, y - 10, label, size=MIN_SIZE, fill=color, maxw=400)

    h_lane(200, C_ROK, True, "РОК: ЦО → СПб")
    h_lane(236, C_RBOK, True, "РБОК: ЦО → СПб")
    h_lane(272, C_RBOK, False, "РБОК: СПб → ЦО")
    h_lane(308, C_RKD, False, "РКД: СПб → ЦО")

    # ---------------- коридор «Казань — consol» (нижний) ------------------
    h_lane(600, C_RBOK, True, "РБОК: Казань → consol")
    h_lane(636, C_RBOK, False, "РБОК: consol → Казань")
    h_lane(672, C_RKD, True, "РКД: Казань → consol")

    # ---------------- коридор «ЦО — Казань» (левый) -----------------------
    def v_lane(x, color, head_down, label, maxw=126):
        if head_down:
            s.arrow([(x, 400), (x, 560)], color, head_end=True,
                    name=f"наконечник {label}")
        else:
            s.arrow([(x, 560), (x, 400)], color, head_end=True,
                    name=f"наконечник {label}")
        s.text(x + 16, 470, label, size=MIN_SIZE, fill=color, anchor="start",
               maxw=maxw)

    v_lane(70, C_ROK, True, "РОК ↓")
    v_lane(190, C_RBOK, True, "РБОК ↓")
    v_lane(310, C_RBOK, False, "РБОК ↑")
    v_lane(430, C_RKD, False, "РКД ↑")

    # ---------------- коридор «СПб — consol» (правый) ---------------------
    def v_lane_r(x, color, head_down, label, maxw=96):
        if head_down:
            s.arrow([(x, 400), (x, 560)], color, head_end=True,
                    name=f"наконечник {label}")
        else:
            s.arrow([(x, 560), (x, 400)], color, head_end=True,
                    name=f"наконечник {label}")
        s.text(x + 16, 470, label, size=MIN_SIZE, fill=color, anchor="start",
               maxw=maxw)

    v_lane_r(1280, C_RBOK, True, "РБОК ↓")
    v_lane_r(1420, C_RBOK, False, "РБОК ↑")
    v_lane_r(1560, C_RKD, True, "РКД ↓")

    # ---------------- дальние пары: ортогональные трассы ------------------
    # РБОК ЦО <-> consol: двунаправленно, два наконечника на расстоянии
    s.arrow([(620, 400), (620, 430), (1230, 430), (1230, 560)], C_RBOK,
            head_end=True, head_start=True, name="РБОК ЦО<->consol")
    s.text(650, 420, "РБОК: ЦО ⇄ consol", size=MIN_SIZE, fill=C_RBOK,
           anchor="start", maxw=250)

    # РОК ЦО -> consol (одно направление)
    s.arrow([(560, 400), (560, 470), (1070, 470), (1070, 560)], C_ROK,
            head_end=True, name="РОК ЦО->consol")
    s.text(650, 460, "РОК: ЦО → consol", size=MIN_SIZE, fill=C_ROK,
           anchor="start", maxw=235)

    # РБОК СПб <-> Казань (через столбцовый коридор, две головки)
    s.arrow([(1130, 400), (1130, 520), (630, 520), (630, 560)], C_RBOK,
            head_end=True, head_start=True, name="РБОК СПб<->Казань")
    s.text(650, 550, "РБОК: СПб ⇄ Казань", size=MIN_SIZE, fill=C_RBOK,
           anchor="start", maxw=265)

    # ---------------- легенда --------------------------------------------
    LX, LY, LW, LH = 40, 882, 1620, 112
    s.rect(LX, LY, LW, LH, fill="#ffffff", stroke=C_NEU_S, sw=1.6, rx=12,
           kind="block", name="легенда", container=True)
    legend = [
        (C_ROK, False, "РОК — с основной копией",
         "ЦО (мастер) → филиалы, consol"),
        (C_RBOK, True, "РБОК — без основной копии",
         "все узлы ⇄ все узлы (РИ)"),
        (C_RKD, False, "РКД — с консолидацией",
         "филиалы → ЦО, consol (своды)"),
    ]
    entry_x = LX + 26
    entry_w = 520
    for color, two_way, t1, t2 in legend:
        flow_icon(s, entry_x, LY + 44, color, two_way, ln=88)
        s.text(entry_x + 108, LY + 36, t1, size=MIN_SIZE, anchor="start",
               fill=color, maxw=entry_w - 118)
        s.text(entry_x + 108, LY + 66, t2, size=MIN_SIZE, anchor="start",
               fill="#374151", maxw=entry_w - 118)
        entry_x += entry_w

    gx = LX + 26
    gx += s.text(gx, LY + 100, "Группы данных:",
                 size=MIN_SIZE, anchor="start", fill="#374151") + 26
    for (name, gf, gs), short in zip(groups, ["НСИ", "Клиенты", "Экземпляры техники",
                                              "Заявки", "Договоры и платежи",
                                              "Обслуживание"]):
        swatch(s, gx, LY + 84, gf, gs, f"группа {name}")
        w = s.text(gx + 26, LY + 100, short, size=MIN_SIZE, anchor="start",
                   maxw=280)
        gx += 26 + w + 30
    if gx - 30 > LX + LW - 20:
        s.fit.append(f"легенда групп не влезает: правый край {gx - 30:.0f}")

    return problems_report(s, "05c_fragmentation_cards")


# ==========================================================================
# ВАРИАНТ B — просторная матрица + панель потоков (1700 x 1000)
# ==========================================================================
def d05d_fragmentation_matrix():
    s = Svg(1700, 1000, "Фрагментация: матрица")
    title_block(
        s,
        "Схема фрагментации РБД «CampusRent»: группы данных × узлы",
        "Вариант B: просторная матрица (зазор 30–44 px, кегль 26 px); "
        "стрелки вынесены в панель «Потоки данных» внизу")

    # ---------------- геометрия матрицы ----------------------------------
    LBL_X, LBL_W = 40, 400
    COLS = [484, 788, 1092, 1396]
    COL_W = 264
    HDR_Y, HDR_H = 100, 110
    ROW_Y0, ROW_H, ROW_GAP = 240, 70, 30

    node_head = [
        ("Центральный", "офис", "HQ · Москва", C_HQ_F, C_HQ_S),
        ("Филиал СПб", None, "Санкт-Петербург", C_NEU_F, C_NEU_S),
        ("Филиал Казань", None, "Казань · KZN", C_NEU_F, C_NEU_S),
        ("Узел", "консолидации", "consol · аналитика", C_CTR_F, C_CTR_S),
    ]

    s.rect(LBL_X, HDR_Y, LBL_W, HDR_H, fill=C_NEU_F, stroke=C_NEU_S, sw=2.4,
           rx=12, kind="block", name="шапка «Группы данных»")
    s.text(LBL_X + LBL_W / 2, HDR_Y + 48, "Группы данных", size=HEAD_SIZE,
           weight="bold", anchor="middle", fill="#374151", maxw=LBL_W - 40)
    s.text(LBL_X + LBL_W / 2, HDR_Y + 84, "и метод поддержки", size=MIN_SIZE,
           anchor="middle", fill="#374151", maxw=LBL_W - 40)
    for k, (l1, l2, sub, f, st) in enumerate(node_head):
        x = COLS[k]
        s.rect(x, HDR_Y, COL_W, HDR_H, fill=f, stroke=st, sw=2.4, rx=12,
               kind="block", name=f"шапка узла {l1} {l2 or ''}")
        if l2:
            s.text(x + COL_W / 2, HDR_Y + 40, l1, size=HEAD_SIZE, weight="bold",
                   fill=st, maxw=COL_W - 20)
            s.text(x + COL_W / 2, HDR_Y + 74, l2, size=HEAD_SIZE, weight="bold",
                   fill=st, maxw=COL_W - 20)
            s.text(x + COL_W / 2, HDR_Y + 100, sub, size=MIN_SIZE,
                   fill="#374151", maxw=COL_W - 16)
        else:
            s.text(x + COL_W / 2, HDR_Y + 58, l1, size=HEAD_SIZE, weight="bold",
                   fill=st, maxw=COL_W - 16)
            s.text(x + COL_W / 2, HDR_Y + 94, sub, size=MIN_SIZE,
                   fill="#374151", maxw=COL_W - 16)

    # ---------------- строки матрицы --------------------------------------
    rows = [
        ("НСИ и справочники", "РОК · снимки 1 раз/сут", C_REF_F, C_REF_S, [
            ("основная копия", "мастер-источник"),
            ("реплика", "снимок 1 раз/сут"),
            ("реплика", "снимок 1 раз/сут"),
            ("реплика", "снимок 1 раз/сут"),
        ]),
        ("Клиенты и подразделения", "РБОК · асинхронное РИ", C_CLI_F, C_CLI_S, [
            ("реплика", "РБОК (РИ)"),
            ("реплика", "РБОК (РИ)"),
            ("реплика", "РБОК (РИ)"),
            ("реплика", "РБОК (РИ)"),
        ]),
        ("Экземпляры техники", "фрагментация EQ_BR+РКД", C_EQ_F, C_EQ_S, [
            ("консолидированная", "копия"),
            ("фрагмент", "EQ_BR = СПб"),
            ("фрагмент", "EQ_BR = Казань"),
            ("консолидированная", "копия"),
        ]),
        ("Заявки и позиции заявок", "РКД + рабочий поток", C_REQ_F, C_REQ_S, [
            ("согласование", "в ЦО"),
            ("рабочая копия", "филиал ⇄ ЦО"),
            ("рабочая копия", "филиал ⇄ ЦО"),
            ("консолидированная", "копия"),
        ]),
        ("Договоры и платежи", "локально + РКД, выдачи", C_CTR_F, C_CTR_S, [
            ("консолидированная", "копия (бухгалтерия)"),
            ("рабочая копия", "филиал"),
            ("рабочая копия", "филиал"),
            ("консолидированная", "копия"),
        ]),
        ("Обслуживание и ремонт", "локально + РКД, затраты", C_SRV_F, C_SRV_S, [
            ("сводный учёт", "затрат"),
            ("рабочая копия", "филиал"),
            ("рабочая копия", "филиал"),
            ("консолидированная", "копия"),
        ]),
    ]

    for i, (name, method, f, st, cells) in enumerate(rows):
        y = ROW_Y0 + i * (ROW_H + ROW_GAP)
        s.rect(LBL_X, y, LBL_W, ROW_H, fill=f, stroke=st, sw=2.4, rx=10,
               kind="block", name=f"строка {name}")
        s.text(LBL_X + 22, y + 30, name, size=MIN_SIZE, weight="bold",
               anchor="start", fill=st, maxw=LBL_W - 44)
        s.text(LBL_X + 22, y + 58, method, size=MIN_SIZE, anchor="start",
               fill="#374151", maxw=LBL_W - 44)
        for j, (l1, l2) in enumerate(cells):
            x = COLS[j]
            s.rect(x, y, COL_W, ROW_H, fill="#ffffff", stroke=st, sw=2, rx=10,
                   kind="block", name=f"ячейка «{name}» / узел {j + 1}")
            s.text(x + COL_W / 2, y + 30, l1, size=MIN_SIZE, anchor="middle",
                   fill="#111827", maxw=COL_W - 12)
            s.text(x + COL_W / 2, y + 58, l2, size=MIN_SIZE, anchor="middle",
                   fill="#4b5563", maxw=COL_W - 12)

    # ---------------- панель «Потоки данных» ------------------------------
    PY, PH = 840, 155
    s.rect(40, PY, 1620, PH, fill="#ffffff", stroke=C_NEU_S, sw=1.6, rx=12,
           kind="block", name="панель потоков", container=True)
    s.text(66, PY + 36, "Потоки данных между узлами (внутри матрицы стрелок "
                        "нет — они вынесены сюда):",
           size=MIN_SIZE, weight="bold", anchor="start", fill="#374151",
           maxw=1560)

    flows = [
        (C_ROK, False,
         "РОК — репликация с основной копией: ЦО (мастер) → филиалы и consol; "
         "снимки 1 раз в сутки"),
        (C_RBOK, True,
         "РБОК — репликация без основной копии: все узлы ⇄ все узлы "
         "(асинхронно, каждый с каждым)"),
        (C_RKD, False,
         "РКД — репликация с консолидацией: филиалы → ЦО и consol; "
         "сводные копии для аналитики"),
    ]
    for k, (color, two_way, txt) in enumerate(flows):
        y = PY + 80 + k * 32
        flow_icon(s, 76, y - 8, color, two_way, ln=110)
        s.text(206, y, txt, size=MIN_SIZE, anchor="start", fill=color,
               maxw=1400)

    return problems_report(s, "05d_fragmentation_matrix")


# ==========================================================================
def problems_report(s, name):
    problems = s.check()
    write(s, name)
    return problems


def write(s, name):
    svg_path = os.path.join(OUT, name + ".svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(s.render())
    png_path = os.path.join(OUT, name + ".png")
    subprocess.run(["rsvg-convert", "-w", str(s.w), svg_path, "-o", png_path],
                   check=True)
    print(f"  {name}.svg / .png  ({s.w}x{s.h})")


def main():
    only = sys.argv[1].upper() if len(sys.argv) > 1 else None
    print("CampusRent: схема фрагментации, вариант 3")
    problems = []
    if only in (None, "A"):
        problems += d05c_fragmentation_cards()
    if only in (None, "B"):
        problems += d05d_fragmentation_matrix()
    if problems:
        print("\nПРОБЛЕМЫ ВЁРСТКИ:")
        for p in problems:
            print("  !", p)
        return 1
    print("\nАвтопроверка: наложений блоков, текста, линий и наконечников нет; "
          f"минимальный зазор {MIN_BLOCK_GAP} px соблюдён.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
