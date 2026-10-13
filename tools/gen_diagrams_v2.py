#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — КРУПНЫЕ (читаемые на слайде) версии двух схем.

Создаёт ТОЛЬКО два файла (старые схемы не трогает):

  diagrams/03b_db_schema_groups.svg / .png — «Схема базы данных по подсистемам»
      1700 x 1100. 22 таблицы собраны в 6 крупных блоков-подсистем,
      между блоками — стрелки с подписями основных связей.

  diagrams/05b_fragmentation.svg / .png — «Схема фрагментации»
      1700 x 1000. Матрица 6 групп таблиц x 4 узла, в ячейках — способ
      поддержки, стрелки направления данных, внизу легенда РОК / РБОК / РКД.

Требования к читаемости: полотно 1700 px, минимальный кегль 26 px,
заголовки 30 px и более, белый фон, пастельные заливки по группам.

SVG генерируется чистым Python, PNG — командой
    rsvg-convert -w 1700 файл.svg -o файл.png

Запуск:  python3 tools/gen_diagrams_v2.py
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "diagrams")

FONT = "Helvetica, Arial, sans-serif"

# --------------------------------------------------------------------------
# Палитра (та же, что в tools/gen_diagrams.py) + фиолетовый для «Сервиса»
# --------------------------------------------------------------------------
C_LINE = "#1f2937"
C_REF_F, C_REF_S = "#dbeafe", "#1d4ed8"   # НСИ — синий
C_CLI_F, C_CLI_S = "#dcfce7", "#15803d"   # клиенты — зелёный
C_EQ_F, C_EQ_S = "#fef9c3", "#a16207"     # техника — жёлтый
C_REQ_F, C_REQ_S = "#fee2e2", "#b91c1c"   # аренда/заявки — красный
C_CTR_F, C_CTR_S = "#ffedd5", "#c2410c"   # договоры — оранжевый
C_SRV_F, C_SRV_S = "#ede9fe", "#6d28d9"   # сервис — фиолетовый
C_NEU_F, C_NEU_S = "#f3f4f6", "#4b5563"   # нейтральный
C_HQ_F, C_HQ_S = "#e0e7ff", "#3730a3"     # персонал / ЦО

MIN_SIZE = 26          # минимальный кегль в SVG
HEAD_SIZE = 30         # заголовки блоков


# --------------------------------------------------------------------------
# Измерение ширины строки тем же шрифтом, которым рисует rsvg-convert
# --------------------------------------------------------------------------
_FONT_CACHE = {}
_FONT_FILES = {
    False: ("/System/Library/Fonts/Helvetica.ttc", 0),
    True: ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
}
SAFETY = 1.02          # запас на различие метрик шрифтов (проверено по рендеру)


def _font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        from PIL import ImageFont
        path, idx = _FONT_FILES[bold]
        _FONT_CACHE[key] = ImageFont.truetype(path, size, index=idx)
    return _FONT_CACHE[key]


def tw(text, size, bold=False):
    """Ширина строки в px (с небольшим запасом)."""
    return _font(size, bold).getlength(text) * SAFETY


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------
# SVG-документ
# --------------------------------------------------------------------------
class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts = []
        self.text_boxes = []     # (x0, y0, x1, y1, text) — для автопроверки
        self.segments = []       # (x1, y1, x2, y2)        — для автопроверки
        self.colors = set()
        self.fit_problems = []   # текст шире отведённого места

    # --- примитивы --------------------------------------------------------
    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=C_LINE, sw=2, rx=12, dash=None):
        d = ' stroke-dasharray="10 7"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=MIN_SIZE, anchor="middle", weight="normal",
             fill="#111827", italic=False, measure=True, maxw=None):
        if size < MIN_SIZE:
            raise ValueError(f"кегль {size} < {MIN_SIZE}: {s!r}")
        st = ' font-style="italic"' if italic else ""
        bold = (weight == "bold")
        w = tw(s, size, bold)
        if maxw is not None and w > maxw:
            self.fit_problems.append(
                f"текст шире места ({w:.0f} > {maxw:.0f}): {s!r}")
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{st}>'
                 f'{esc(s)}</text>')
        if measure:
            if anchor == "start":
                x0 = x
            elif anchor == "end":
                x0 = x - w
            else:
                x0 = x - w / 2.0
            asc, desc = _font(size, bold).getmetrics()
            self.text_boxes.append((x0, y - asc, x0 + w, y + desc, s))
        return w

    def line(self, x1, y1, x2, y2, stroke=C_LINE, sw=2, dash=None,
             marker=False, marker_start=False, record=True):
        d = ' stroke-dasharray="10 7"' if dash else ""
        m = ""
        if marker:
            m += f' marker-end="url(#{self._mid(stroke)})"'
        if marker_start:
            m += f' marker-start="url(#{self._mid(stroke)})"'
        self.colors.add(stroke)
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}{m}/>')
        if record:
            self.segments.append((x1, y1, x2, y2, sw))

    def _mid(self, color):
        return "arw" + color.lstrip("#")

    # --- сборка файла -----------------------------------------------------
    def _defs(self):
        out = ['<defs>']
        for c in sorted(self.colors):
            out.append(
                f'<marker id="{self._mid(c)}" viewBox="0 0 10 10" refX="9" refY="5" '
                f'markerWidth="18" markerHeight="18" orient="auto-start-reverse">'
                f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>')
        out.append('</defs>')
        return "".join(out)

    def render(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'{self._defs()}'
                f'<rect width="100%" height="100%" fill="#ffffff"/>')
        return head + "\n" + "\n".join(self.parts) + "\n</svg>\n"

    def check(self):
        """Автопроверка: текст не выходит за полотно, тексты не наложены,
        текст не лежит на линиях."""
        problems = []
        problems.extend(self.fit_problems)
        for (x0, y0, x1, y1, t) in self.text_boxes:
            if x0 < 0 or y0 < 0 or x1 > self.w or y1 > self.h:
                problems.append(f"за полотном: {t!r} bbox=({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})")
        tb = self.text_boxes
        for i in range(len(tb)):
            for j in range(i + 1, len(tb)):
                a, b = tb[i], tb[j]
                if a[0] < b[2] - 1 and b[0] < a[2] - 1 and a[1] < b[3] - 1 and b[1] < a[3] - 1:
                    problems.append(f"наложение текста: {a[4]!r} <-> {b[4]!r}")
        for (x0, y0, x1, y1, t) in tb:
            for (sx1, sy1, sx2, sy2, sw) in self.segments:
                if _seg_rect_hit(sx1, sy1, sx2, sy2, x0 + 2, y0 + 2, x1 - 2, y1 - 2):
                    problems.append(f"текст на линии: {t!r} линия ({sx1:.0f},{sy1:.0f})-({sx2:.0f},{sy2:.0f})")
        return problems


def _seg_rect_hit(x1, y1, x2, y2, rx0, ry0, rx1, ry1):
    """Пересекается ли отрезок с прямоугольником (алгоритм Лианга—Барски)."""
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


def center(r):
    x, y, w, h = r
    return (x + w / 2.0, y + h / 2.0)


# --------------------------------------------------------------------------
# 03b. СХЕМА БД ПО ПОДСИСТЕМАМ (1700 x 1100)
# --------------------------------------------------------------------------
def d03b_db_schema_groups():
    s = Svg(1700, 1100, "Схема БД по подсистемам")
    s.text(50, 54, "Схема базы данных «CampusRent»: подсистемы и основные связи",
           size=36, weight="bold", anchor="start")
    s.text(50, 96, "22 таблицы собраны в 6 подсистем; стрелки — основные связи 1 — N; "
                   "цвет — подсистема", size=MIN_SIZE, fill="#4b5563", anchor="start")

    # ---------- 1. НСИ и номенклатура (верхний широкий блок) -------------
    # Верх блока — 118 (а не 112): до подзаголовка остаётся 14 px зазора.
    bx, by, bw, bh = 40, 118, 1620, 222
    s.rect(bx, by, bw, bh, fill=C_REF_F, stroke=C_REF_S, sw=3, rx=16)
    s.text(bx + 26, by + 44, "НСИ и номенклатура", size=HEAD_SIZE, weight="bold",
           anchor="start", fill=C_REF_S)
    s.text(bx + bw - 26, by + 44, "10 таблиц · справочники-источники (РОК)",
           size=MIN_SIZE, anchor="end", fill="#374151")
    nsi = ["branches", "categories", "models", "model_components", "model_purposes",
           "tariffs", "request_statuses", "payment_methods", "maintenance_types",
           "condition_grades"]
    for i, name in enumerate(nsi):
        r, c = divmod(i, 5)
        s.text(bx + 26 + c * 320, by + 122 + r * 64, name, size=MIN_SIZE,
               anchor="start", maxw=300)

    # ---------- 2-й ряд: Клиенты | Персонал | Техника --------------------
    r2y, r2h = 480, 220
    cli = (40, r2y, 500, r2h)
    per = (580, r2y, 500, r2h)
    teq = (1105, r2y, 555, r2h)

    s.rect(*cli, fill=C_CLI_F, stroke=C_CLI_S, sw=3, rx=16)
    s.text(cli[0] + 26, cli[1] + 44, "Клиенты", size=HEAD_SIZE, weight="bold",
           anchor="start", fill=C_CLI_S)
    s.text(cli[0] + cli[2] - 26, cli[1] + 44, "3 таблицы", size=MIN_SIZE,
           anchor="end", fill="#374151")
    for i, name in enumerate(["universities", "departments", "representatives"]):
        s.text(cli[0] + 26, cli[1] + 105 + i * 45, name, size=MIN_SIZE,
               anchor="start", maxw=cli[2] - 52)

    s.rect(*per, fill=C_HQ_F, stroke=C_HQ_S, sw=3, rx=16)
    s.text(per[0] + 26, per[1] + 44, "Персонал", size=HEAD_SIZE, weight="bold",
           anchor="start", fill=C_HQ_S)
    s.text(per[0] + per[2] - 26, per[1] + 44, "1 таблица", size=MIN_SIZE,
           anchor="end", fill="#374151")
    s.text(per[0] + 26, per[1] + 105, "employees", size=MIN_SIZE, anchor="start",
           maxw=per[2] - 52)
    s.text(per[0] + 26, per[1] + 150, "(сотрудники филиалов)", size=MIN_SIZE,
           anchor="start", fill="#4b5563", maxw=per[2] - 52)

    s.rect(*teq, fill=C_EQ_F, stroke=C_EQ_S, sw=3, rx=16)
    s.text(teq[0] + 26, teq[1] + 44, "Техника", size=HEAD_SIZE, weight="bold",
           anchor="start", fill=C_EQ_S)
    s.text(teq[0] + teq[2] - 26, teq[1] + 44, "2 таблицы", size=MIN_SIZE,
           anchor="end", fill="#374151")
    s.text(teq[0] + 26, teq[1] + 105, "equipment_units", size=MIN_SIZE, anchor="start",
           maxw=teq[2] - 52)
    s.text(teq[0] + 26, teq[1] + 150, "transfers", size=MIN_SIZE, anchor="start",
           maxw=teq[2] - 52)

    # ---------- 3-й ряд: Аренда | Сервис ---------------------------------
    # Высота 160 px (было 180): освобождает место под легенду в две строки.
    r3y, r3h = 840, 160
    are = (40, r3y, 1140, r3h)
    srv = (1250, r3y, 410, r3h)

    s.rect(*are, fill=C_REQ_F, stroke=C_REQ_S, sw=3, rx=16)
    s.text(are[0] + 26, are[1] + 46, "Аренда и договоры", size=HEAD_SIZE, weight="bold",
           anchor="start", fill=C_REQ_S)
    s.text(are[0] + are[2] - 26, are[1] + 46, "5 таблиц · РКД + рабочий поток",
           size=MIN_SIZE, anchor="end", fill="#374151")
    ax = are[0] + 26
    for name in ["requests", "request_items", "contracts", "rentals", "payments"]:
        w = s.text(ax, are[1] + 128, name, size=MIN_SIZE, anchor="start", maxw=260)
        ax += w + 55
    if ax - 55 > are[0] + are[2] - 26:
        s.fit_problems.append("список таблиц «Аренда» не влезает в блок")

    s.rect(*srv, fill=C_SRV_F, stroke=C_SRV_S, sw=3, rx=16)
    s.text(srv[0] + 26, srv[1] + 46, "Сервис", size=HEAD_SIZE, weight="bold",
           anchor="start", fill=C_SRV_S)
    s.text(srv[0] + srv[2] - 26, srv[1] + 46, "1 таблица", size=MIN_SIZE,
           anchor="end", fill="#374151")
    s.text(srv[0] + 26, srv[1] + 128, "maintenance", size=MIN_SIZE, anchor="start",
           maxw=srv[2] - 52)

    # ---------- Полоса связей 1 (НСИ -> ряд 2) ---------------------------
    # Наконечник при sw=2.2: markerWidth=18 * stroke-width => длина 39.6 px,
    # кончик выступает на 4 px за конец линии, основание — в 36 px перед ним.
    # Подпись стоит в разрыве линии: 14 px до верхнего отрезка, 12 px до
    # нижнего, 26 px от низа текста до основания наконечника.
    LINK_SW = 2.2

    def vlink(x, y1, y2, label, color=C_REF_S):
        s.line(x, y1, x, 373, stroke=color, sw=LINK_SW)
        s.line(x, 426, x, y2 - 4, stroke=color, sw=LINK_SW, marker=True)
        s.text(x, 408, label, size=MIN_SIZE)

    vlink(290, by + bh, r2y, "филиал 1 — N ВУЗ")
    vlink(830, by + bh, r2y, "филиал 1 — N сотрудник")
    vlink(1382, by + bh, r2y, "модель 1 — N экземпляр")

    # ---------- Полоса связей 2 (ряд 2 -> ряд 3) ------------------------
    # Все четыре подписи — в один ряд (общая базовая линия y = 770) и слева
    # от своей линии с зазором 24 px: текст (низ 776) не касается ни линии,
    # ни наконечника (основание на 800, кончик упирается в верх блока 840).
    LINK_Y = 770

    def hlink(x, label, color):
        s.line(x, r2y + r2h, x, r3y - 4, stroke=color, sw=LINK_SW, marker=True)
        s.text(x - 24, LINK_Y, label, size=MIN_SIZE, anchor="end")

    hlink(290, "ВУЗ 1 — N заявка", C_CLI_S)
    hlink(640, "сотрудник 1 — N выдача", C_HQ_S)
    # линия идёт из блока «Техника» (1105…1660), а не из зазора между блоками
    hlink(1130, "экземпляр 1 — N позиция заявки", C_EQ_S)
    hlink(1580, "экземпляр 1 — N обслуживание", C_EQ_S)

    # ---------- Легенда: состав подсистем + расшифровка аббревиатур ------
    ly, lh = 1006, 90
    s.rect(40, ly, 1620, lh, fill="#ffffff", stroke=C_NEU_S, sw=1.6, rx=12)
    legend = [(C_REF_F, C_REF_S, "НСИ и номенклатура"), (C_CLI_F, C_CLI_S, "Клиенты"),
              (C_HQ_F, C_HQ_S, "Персонал"), (C_EQ_F, C_EQ_S, "Техника"),
              (C_REQ_F, C_REQ_S, "Аренда и договоры"), (C_SRV_F, C_SRV_S, "Сервис")]
    lx = 66
    for f, st, t in legend:
        s.rect(lx, ly + 11, 26, 26, fill=f, stroke=st, sw=2, rx=5)
        s.text(lx + 38, ly + 32, t, size=MIN_SIZE, anchor="start", maxw=300)
        lx += 38 + tw(t, MIN_SIZE) + 46
    if lx - 46 > 1634:
        s.fit_problems.append(f"легенда не влезает: правый край {lx - 46:.0f} > 1634")
    # Аббревиатуры РОК и РКД встречаются в шапках блоков — расшифровываем
    # их прямо в легенде, чтобы на слайде не осталось необъяснённых сокращений.
    s.text(66, ly + 70, "Обозначения: РОК — репликация с основной копией; "
                        "РКД — репликация с консолидацией",
           size=MIN_SIZE, anchor="start", fill="#374151", maxw=1568)

    problems = s.check()
    write(s, "03b_db_schema_groups")
    return problems

# --------------------------------------------------------------------------
# 05b. СХЕМА ФРАГМЕНТАЦИИ (1700 x 1000)
# --------------------------------------------------------------------------
def d05b_fragmentation():
    s = Svg(1700, 1000, "Схема фрагментации")
    s.text(50, 50, "Схема фрагментации распределённой БД «CampusRent»",
           size=36, weight="bold", anchor="start")
    s.text(50, 88, "Строки — группы таблиц; столбцы — узлы сети; стрелки — направление "
                   "передачи данных; цвет — метод поддержки", size=MIN_SIZE,
           fill="#4b5563", anchor="start")

    # ---------- колонки ---------------------------------------------------
    lab_x, lab_w = 40, 380
    col_w, gap = 273, 36
    cols = [lab_x + lab_w + gap + i * (col_w + gap) for i in range(4)]
    ccen = [c + col_w / 2.0 for c in cols]
    hdr_y, hdr_h = 100, 120
    row_y0, row_h, row_gap = 226, 82, 24
    cell_maxw = col_w - 22
    lab_maxw = lab_w - 24

    s.rect(lab_x, hdr_y, lab_w, hdr_h, fill=C_NEU_F, stroke=C_NEU_S, sw=2, rx=12)
    s.text(lab_x + lab_w / 2, hdr_y + 60, "Группа таблиц", size=HEAD_SIZE,
           weight="bold", fill="#374151", maxw=lab_maxw)

    # Заголовки узлов: имя (30 px, при необходимости в две строки) + подпись
    nodes = [(["Центральный", "офис"], "HQ · Москва", C_HQ_F, C_HQ_S),
             (["Филиал СПб"], "Санкт-Петербург", C_NEU_F, C_NEU_S),
             (["Филиал Казань"], "Казань · KZN", C_NEU_F, C_NEU_S),
             (["Узел", "консолидации"], "consol · аналитика", C_CTR_F, C_CTR_S)]
    for x, (lines, sub, f, st) in zip(cols, nodes):
        s.rect(x, hdr_y, col_w, hdr_h, fill=f, stroke=st, sw=2.4, rx=12)
        if len(lines) == 1:
            s.text(x + col_w / 2, hdr_y + 53, lines[0], size=HEAD_SIZE,
                   weight="bold", fill=st, maxw=cell_maxw)
        else:
            for k, line in enumerate(lines):
                s.text(x + col_w / 2, hdr_y + 35 + k * 36, line, size=HEAD_SIZE,
                       weight="bold", fill=st, maxw=cell_maxw)
        s.text(x + col_w / 2, hdr_y + 105, sub, size=MIN_SIZE, fill="#374151",
               maxw=cell_maxw)

    # ---------- строки ----------------------------------------------------
    rows = [
        ("НСИ и справочники", "РОК · снимки 1/сут", C_REF_F, C_REF_S, "rok",
         [("основная копия", "мастер-источник"), ("реплика", "снимок 1/сут"),
          ("реплика", "снимок 1/сут"), ("реплика", "снимок 1/сут")]),
        ("Клиенты", "РБОК · асинхронное РИ", C_CLI_F, C_CLI_S, "rbok",
         [("реплика", "РБОК (РИ)"), ("реплика", "РБОК (РИ)"),
          ("реплика", "РБОК (РИ)"), ("реплика", "РБОК (РИ)")]),
        ("Экземпляры техники", "фрагментация + РКД", C_EQ_F, C_EQ_S, "rkd",
         [("консолидированная", "копия"), ("фрагмент", "EQ_BR = СПб"),
          ("фрагмент", "EQ_BR = KZN"), ("консолидированная", "копия")]),
        ("Заявки", "РКД + рабочий поток", C_REQ_F, C_REQ_S, "rkd",
         [("основная копия", "+ согласование"), ("рабочая копия", "филиал ↔ ЦО"),
          ("рабочая копия", "филиал ↔ ЦО"), ("консолидированная", "копия")]),
        ("Договоры и платежи", "РКД · финансы", C_CTR_F, C_CTR_S, "rkd",
         [("основная копия", "бухгалтерия"), ("рабочая копия", "филиал"),
          ("рабочая копия", "филиал"), ("консолидированная", "копия")]),
        ("Обслуживание", "РКД · затраты", C_SRV_F, C_SRV_S, "rkd",
         [("основная копия", "сводный учёт"), ("рабочая копия", "филиал"),
          ("рабочая копия", "филиал"), ("консолидированная", "копия")]),
    ]

    for i, (name, method, f, st, mode, cells) in enumerate(rows):
        y = row_y0 + i * (row_h + row_gap)
        s.rect(lab_x, y, lab_w, row_h, fill=f, stroke=st, sw=2.4, rx=12)
        s.text(lab_x + lab_w / 2, y + 34, name, size=HEAD_SIZE, weight="bold",
               fill=st, maxw=lab_maxw)
        s.text(lab_x + lab_w / 2, y + 66, method, size=MIN_SIZE, fill="#374151",
               maxw=lab_maxw)
        for j, (l1, l2) in enumerate(cells):
            s.rect(cols[j], y, col_w, row_h, fill=f, stroke=st, sw=2, rx=12)
            if l2:
                s.text(cols[j] + col_w / 2, y + 36, l1, size=MIN_SIZE,
                       maxw=cell_maxw)
                s.text(cols[j] + col_w / 2, y + 66, l2, size=MIN_SIZE,
                       fill="#374151", maxw=cell_maxw)
            else:
                s.text(cols[j] + col_w / 2, y + 51, l1, size=MIN_SIZE,
                       maxw=cell_maxw)

        # ---- стрелки: РОК — от ЦО ко всем узлам (шина «вещания») --------
        if mode == "rok":
            bus = y + row_h + 13
            s.line(ccen[0], y + row_h, ccen[0], bus, stroke=st, sw=2.2)
            s.line(ccen[0], bus, ccen[3], bus, stroke=st, sw=2.2)
            for x in ccen[1:]:
                s.line(x, bus, x, y + row_h, stroke=st, sw=2.2, marker=True)
        # ---- РБОК — двунаправленная репликация между соседями ----------
        elif mode == "rbok":
            for k in range(3):
                s.line(cols[k] + col_w + 4, y + row_h / 2, cols[k + 1] - 4,
                       y + row_h / 2, stroke=st, sw=2.2, marker=True, marker_start=True)
        # ---- РКД — филиалы собираются в ЦО и в узел консолидации -------
        else:
            bus = y + row_h + 13
            for x in ccen[1:3]:
                s.line(x, y + row_h, x, bus, stroke=st, sw=2.2)
            s.line(ccen[0], bus, ccen[3], bus, stroke=st, sw=2.2)
            for x in (ccen[0], ccen[3]):
                s.line(x, bus, x, y + row_h, stroke=st, sw=2.2, marker=True)

    # ---------- легенда ---------------------------------------------------
    ly, lh = 862, 128
    s.rect(40, ly, 1620, lh, fill="#ffffff", stroke=C_NEU_S, sw=1.6, rx=12)
    legend = [
        (C_REF_F, C_REF_S, "РОК — репликация с основной копией (ЦО — мастер)"),
        (C_CLI_F, C_CLI_S, "РБОК — репликация без основной копии (РИ)"),
        (C_EQ_F, C_EQ_S, "Фрагментация: EQ_BR = узел-владелец"),
        (C_CTR_F, C_CTR_S, "РКД — репликация с консолидацией"),
        (C_REQ_F, C_REQ_S, "Заявки: рабочая копия + согласование в ЦО"),
        (C_SRV_F, C_SRV_S, "Обслуживание: локально + свод в ЦО"),
    ]
    baselines = [ly + 34, ly + 68, ly + 102]
    for k, (f, st, t) in enumerate(legend):
        cx = 62 if k % 2 == 0 else 860
        cy = baselines[k // 2]
        s.rect(cx, cy - 21, 26, 26, fill=f, stroke=st, sw=2, rx=5)
        s.text(cx + 38, cy, t, size=MIN_SIZE, anchor="start", maxw=740)

    problems = s.check()
    write(s, "05b_fragmentation")
    return problems


# --------------------------------------------------------------------------
def write(s, name):
    svg_path = os.path.join(OUT, name + ".svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(s.render())
    png_path = os.path.join(OUT, name + ".png")
    subprocess.run(["rsvg-convert", "-w", str(s.w), svg_path, "-o", png_path],
                   check=True)
    print(f"  {name}.svg / .png  ({s.w}x{s.h})")


def main():
    print("CampusRent: генерация читаемых схем (v2)")
    problems = []
    problems += d03b_db_schema_groups()
    problems += d05b_fragmentation()
    if problems:
        print("\nПРОБЛЕМЫ ВЁРСТКИ:")
        for p in problems:
            print("  !", p)
        return 1
    print("\nАвтопроверка: наложений текста и пересечений текста с линиями нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
