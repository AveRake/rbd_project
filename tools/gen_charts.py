#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — генератор графиков по результатам запросов (SVG → PNG).

Графики используются в итоговом отчёте (results/graphs/chart_*.png).
Запуск:  python3 tools/gen_charts.py
Скрипт пишет SVG и сразу рендерит PNG через rsvg-convert -w 1600
(если rsvg-convert нет в PATH — остаются только SVG).

Оформление (единый стиль):
  * подписи осей и единицы измерения (₽, шт., дней, раз);
  * числа в русском формате: пробел — разделитель тысяч, запятая — десятичная
    («4 000 000», «19,1»), а не английское «4,000,000»;
  * коды филиалов расшифрованы (HQ — Москва и т. д.);
  * в круговой диаграмме все секторы разного цвета, соседние — контрастные
    (проверяется функцией check_pie_colors);
  * неполный месяц в динамике показывается пунктиром и помечается текстом.
"""

import math
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "graphs")

PNG_WIDTH = 1600  # ширина PNG (Slide/Word масштабируют до ~1000 px)

FONT = "Helvetica, Arial, sans-serif"
TXT = "#111111"
MUTED = "#555555"
AXIS = "#bfbfbf"
GRID = "#d9d9d9"

# Палитра рядов для столбчатых диаграмм (фирменный синий ряд).
SERIES = ["#1f4e79", "#2e75b6", "#9dc3e6", "#c9c9c9", "#8faadc", "#44546a", "#bdd7ee"]

# Палитра круговой диаграммы: 7 РАЗНЫХ цветов.
# Порядок подобран так, чтобы любые два соседних сектора (включая замыкание
# последнего сектора на первый) различались и по светлоте, и по тону.
# Проверка: check_pie_colors() — минимальный контраст соседей >= 2,0,
# минимальная разница тонов >= 25 градусов.
PIE_COLORS = [
    "#1F4E79",  # 1 Компьютерная техника      — тёмно-синий
    "#F2C14E",  # 2 Лабораторное оборудование — янтарный
    "#4E8A5F",  # 3 Проекционное оборудование — зелёный
    "#BFBFBF",  # 4 Сетевое оборудование      — серый
    "#7D5BA6",  # 5 Аудио- и видеооборудование— фиолетовый
    "#BDD7EE",  # 6 VR/AR-оборудование        — светло-голубой
    "#2E8B8B",  # 7 Оргтехника и печать       — бирюзовый
]

# Расшифровка кодов филиалов (используется в подписях категорий).
BRANCH = {
    "HQ": "Москва",
    "SPB": "Санкт-Петербург",
    "KZN": "Казань",
    "NSK": "Новосибирск",
}


def branch_label(code):
    """'HQ' → 'HQ\\nМосква' (код + расшифровка для подписи категории)."""
    return f"{code}\n{BRANCH[code]}" if code in BRANCH else code


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- числа
def ru(v, dec=0):
    """Русский формат числа: 1234567 → '1 234 567', 19.14 → '19,1'."""
    s = f"{v:,.{dec}f}".replace(",", " ")  # пробел — разделитель тысяч
    return s.replace(".", ",") if dec else s


def ru_int(v):
    return ru(v, 0)


def ru_short(v):
    """Компактная подпись с русской запятой: '3,8 млн', '800 тыс'."""
    if v >= 1_000_000:
        return f"{ru(v / 1_000_000, 1)} млн"
    if v >= 1000:
        return f"{ru(v / 1000, 0)} тыс"
    return ru(v, 0)


def nice_max(v):
    if v <= 0:
        return 10
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * exp:
            return m * exp
    return 10 * exp


def wrap_lines(text, width=14, maxlines=3):
    """Разбивает подпись на строки, сохраняя явные переносы \"\\n\"."""
    out = []
    for part in str(text).split("\n"):
        cur = ""
        for wd in part.split():
            if len(cur) + len(wd) + 1 <= width:
                cur = (cur + " " + wd).strip()
            else:
                if cur:
                    out.append(cur)
                cur = wd
        if cur:
            out.append(cur)
    return out[:maxlines]


# ---------------------------------------------------------------- цвета
def _srgb(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(color):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def contrast(a, b):
    """Коэффициент контраста (WCAG), 1.0 … 21.0."""
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _hue(color):
    r, g, b = (int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0.0
    d = mx - mn
    if mx == r:
        h = (60 * ((g - b) / d)) % 360
    elif mx == g:
        h = 60 * ((b - r) / d) + 120
    else:
        h = 60 * ((r - g) / d) + 240
    return h


def _hue_delta(a, b):
    d = abs(_hue(a) - _hue(b))
    return min(d, 360 - d)


def check_pie_colors(colors=PIE_COLORS, min_contrast=2.0, min_hue=25.0):
    """Проверяет уникальность цветов и контраст соседних секторов (циклически)."""
    assert len(set(colors)) == len(colors), "в круговой диаграмме есть одинаковые цвета!"
    pairs = []
    for i in range(len(colors)):
        a, b = colors[i], colors[(i + 1) % len(colors)]
        pairs.append((i + 1, (i + 1) % len(colors) + 1, contrast(a, b), _hue_delta(a, b)))
    bad = [p for p in pairs if p[2] < min_contrast or p[3] < min_hue]
    print("Круговая диаграмма: цветов %d, все уникальны." % len(colors))
    for a, b, cr, hd in pairs:
        print("  сектор %d→%d: контраст %.2f, разница тонов %.0f°" % (a, b, cr, hd))
    assert not bad, "соседние секторы недостаточно контрастны: %s" % bad
    return pairs


def label_on(fill):
    """Цвет подписи поверх заливки: белый на тёмной, тёмный на светлой."""
    return "#ffffff" if contrast(fill, "#ffffff") >= 3.0 else TXT


# ---------------------------------------------------------------- SVG
class Chart:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.p = []

    def add(self, s):
        self.p.append(s)

    def text(self, x, y, s, size=14, anchor="middle", weight="normal", fill=TXT, rotate=None):
        tr = f' transform="rotate({rotate} {x} {y})"' if rotate else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{tr}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=GRID, sw=1, dash=None):
        d = ' stroke-dasharray="4 4"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=0):
        self.add(f'<rect x="{x}" y="{y}" width="{max(w,0)}" height="{max(h,0)}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def path(self, d, fill, stroke="#ffffff", sw=2):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def header(self):
        self.text(40, 46, self.title, size=22, anchor="start", weight="bold")

    def axis_titles(self, cx, ylabel, xlabel, x_y, y_x=34):
        """Подписи осей: Y — повёрнутая слева, X — по центру под шкалой."""
        if ylabel:
            self.text(y_x, cx, ylabel, size=15, rotate=-90, fill=TXT)
        if xlabel:
            self.text(cx, x_y, xlabel, size=15, fill=TXT)

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="#ffffff"/>')
        svg_path = os.path.join(OUT, name)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(head + "\n" + "\n".join(self.p) + "\n</svg>\n")
        png_path = os.path.splitext(svg_path)[0] + ".png"
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-w", str(PNG_WIDTH), svg_path, "-o", png_path],
                           check=True)
        else:
            print("rsvg-convert не найден — PNG не создан: " + png_path, file=sys.stderr)
        return svg_path


# ---------------------------------------------------------------- графики
def bar_v(name, title, cats, values, note="", xlabel=None, ylabel=None,
          color=None, w=1100, h=620, label_fmt=ru_int, tick_fmt=ru_int):
    """Вертикальные столбцы с подписями осей."""
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 160, 40, 100, 134
    pw, ph = w - L - R, h - T - B
    vmax = nice_max(max(values))
    for i in range(6):
        y = T + ph - ph * i / 5
        c.line(L, y, L + pw, y)
        c.text(L - 12, y + 5, tick_fmt(vmax * i / 5), size=14, anchor="end", fill=MUTED)
    c.line(L, T, L, T + ph, stroke=AXIS)
    c.line(L, T + ph, L + pw, T + ph, stroke=AXIS)
    bw = pw / len(cats)
    for i, (cat, v) in enumerate(zip(cats, values)):
        bh = ph * v / vmax
        x = L + i * bw + bw * 0.18
        c.rect(x, T + ph - bh, bw * 0.64, bh, color or SERIES[i % len(SERIES)])
        c.text(L + i * bw + bw / 2, T + ph - bh - 12, label_fmt(v), size=14, weight="bold")
        for k, ln in enumerate(wrap_lines(cat)):
            c.text(L + i * bw + bw / 2, T + ph + 30 + k * 19, ln, size=14)
    c.axis_titles(T + ph / 2, ylabel, xlabel, h - 46)
    if note:
        c.text(L, h - 14, note, size=12, anchor="start", fill=MUTED)
    c.save(name)


def bar_h(name, title, cats, values, note="", xlabel=None, color=None,
          w=1100, h=640, label_fmt=ru_int, tick_fmt=ru_int, cat_w=330):
    """Горизонтальные столбцы (категории подписаны слева)."""
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = cat_w, 90, 100, 100
    pw, ph = w - L - R, h - T - B
    vmax = nice_max(max(values))
    rh = ph / len(cats)
    for i, (cat, v) in enumerate(zip(cats, values)):
        y = T + i * rh
        c.rect(L, y + rh * 0.16, pw * v / vmax, rh * 0.62, color or SERIES[i % len(SERIES)])
        c.text(L - 12, y + rh * 0.55, cat, size=14, anchor="end")
        c.text(L + pw * v / vmax + 12, y + rh * 0.55, label_fmt(v), size=14,
               anchor="start", weight="bold")
    for i in range(6):
        x = L + pw * i / 5
        c.line(x, T, x, T + ph, stroke=GRID)
        c.text(x, T + ph + 27, tick_fmt(vmax * i / 5), size=14, fill=MUTED)
    c.line(L, T, L, T + ph, stroke=AXIS)
    c.line(L, T + ph, L + pw, T + ph, stroke=AXIS)
    if xlabel:
        c.text(L + pw / 2, h - 46, xlabel, size=15)
    if note:
        c.text(L, h - 14, note, size=12, anchor="start", fill=MUTED)
    c.save(name)


def bar_stacked(name, title, cats, series, note="", xlabel=None, ylabel=None,
                w=1100, h=620, tick_fmt=ru_int):
    """series: list of (name, values)."""
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 120, 280, 100, 134
    pw, ph = w - L - R, h - T - B
    totals = [sum(s[1][i] for s in series) for i in range(len(cats))]
    vmax = nice_max(max(totals))
    for i in range(6):
        y = T + ph - ph * i / 5
        c.line(L, y, L + pw, y)
        c.text(L - 12, y + 5, tick_fmt(vmax * i / 5), size=14, anchor="end", fill=MUTED)
    c.line(L, T, L, T + ph, stroke=AXIS)
    c.line(L, T + ph, L + pw, T + ph, stroke=AXIS)
    bw = pw / len(cats)
    for i, cat in enumerate(cats):
        acc = 0
        for k, (sname, vals) in enumerate(series):
            bh = ph * vals[i] / vmax
            c.rect(L + i * bw + bw * 0.2, T + ph - acc - bh, bw * 0.6, bh, SERIES[k])
            acc += bh
        c.text(L + i * bw + bw / 2, T + ph - acc - 12, tick_fmt(totals[i]), size=14, weight="bold")
        for k, ln in enumerate(wrap_lines(cat, 16)):
            c.text(L + i * bw + bw / 2, T + ph + 30 + k * 19, ln, size=14)
    # легенда
    for k, (sname, _vals) in enumerate(series):
        y = T + 10 + k * 32
        c.rect(L + pw + 40, y, 22, 18, SERIES[k])
        c.text(L + pw + 74, y + 14, sname, size=14, anchor="start")
    c.axis_titles(T + ph / 2, ylabel, xlabel, h - 46)
    if note:
        c.text(L, h - 14, note, size=12, anchor="start", fill=MUTED)
    c.save(name)


def pie(name, title, cats, values, note="", w=1000, h=660):
    """Круговая диаграмма: каждому сектору свой различимый цвет."""
    check_pie_colors(PIE_COLORS[:len(cats)])
    c = Chart(w, h, title)
    c.header()
    cx, cy, r = 330, 360, 195
    total = sum(values)
    ang = -90
    for i, (cat, v) in enumerate(zip(cats, values)):
        a = 360 * v / total
        a1, a2 = math.radians(ang), math.radians(ang + a)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        large = 1 if a > 180 else 0
        fill = PIE_COLORS[i % len(PIE_COLORS)]
        c.path(f"M {cx} {cy} L {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} Z",
               fill)
        mid = math.radians(ang + a / 2)
        lx, ly = cx + r * 0.66 * math.cos(mid), cy + r * 0.66 * math.sin(mid)
        if v / total > 0.06:
            c.text(lx, ly + 5, f"{ru(100 * v / total, 0)}%", size=15, weight="bold",
                   fill=label_on(fill))
        ang += a
    # легенда
    for i, (cat, v) in enumerate(zip(cats, values)):
        y = 150 + i * 38
        fill = PIE_COLORS[i % len(PIE_COLORS)]
        c.rect(620, y, 24, 20, fill)
        c.text(658, y + 15, f"{cat} — {v} ({ru(100 * v / total, 1)}%)",
               size=14, anchor="start")
    c.text(40, h - 24, note or ("Всего: %s экз." % ru_int(total)), size=13,
           anchor="start", fill=MUTED)
    c.save(name)


def line_chart(name, title, cats, values, note="", xlabel=None, ylabel=None,
               w=1200, h=590, tick_fmt=ru_int, label_fmt=ru_int,
               partial_last=False, partial_note=""):
    """Линейный график. partial_last — последняя точка неполного периода."""
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 165, 70, 100, 140
    pw, ph = w - L - R, h - T - B
    vmax = nice_max(max(values))
    for i in range(6):
        y = T + ph - ph * i / 5
        c.line(L, y, L + pw, y)
        c.text(L - 12, y + 5, tick_fmt(vmax * i / 5), size=14, anchor="end", fill=MUTED)
    c.line(L, T, L, T + ph, stroke=AXIS)
    c.line(L, T + ph, L + pw, T + ph, stroke=AXIS)
    n = len(cats)
    step = pw / (n - 1)
    pts = [(L + i * step, T + ph - ph * v / vmax) for i, v in enumerate(values)]
    if partial_last and n > 1:
        # сплошная линия по полным месяцам + пунктирный отрезок к неполному
        c.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="3"/>'
              % (" ".join(f"{x:.1f},{y:.1f}" for x, y in pts[:-1]), SERIES[0]))
        c.add(f'<line x1="{pts[-2][0]:.1f}" y1="{pts[-2][1]:.1f}" '
              f'x2="{pts[-1][0]:.1f}" y2="{pts[-1][1]:.1f}" stroke="{SERIES[0]}" '
              f'stroke-width="3" stroke-dasharray="8 6"/>')
    else:
        c.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="3"/>'
              % (" ".join(f"{x:.1f},{y:.1f}" for x, y in pts), SERIES[0]))
    for i, ((x, y), v) in enumerate(zip(pts, values)):
        # подпись первой точки сдвигаем вправо, чтобы не наезжала на шкалу Y
        anchor = "start" if i == 0 else "middle"
        lx = x + 10 if i == 0 else x
        if partial_last and i == n - 1:
            c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#ffffff" '
                  f'stroke="{SERIES[0]}" stroke-width="3"/>')
            c.text(lx, y - 18, label_fmt(v), size=14, weight="bold", fill=MUTED, anchor=anchor)
        else:
            c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{SERIES[0]}"/>')
            c.text(lx, y - 18, label_fmt(v), size=14, weight="bold", anchor=anchor)
    for i, cat in enumerate(cats):
        c.text(L + i * step, T + ph + 30, cat, size=13, rotate=-30)
    c.axis_titles(T + ph / 2, ylabel, xlabel, h - 50)
    if partial_last and partial_note:
        c.text(L + 10, T + 26, partial_note, size=13, anchor="start", fill=MUTED)
    if note:
        c.text(L, h - 14, note, size=12, anchor="start", fill=MUTED)
    c.save(name)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    bar_stacked("chart_01_fleet_load.svg",
                "Загрузка парка техники по филиалам",
                [branch_label(b) for b in ("HQ", "SPB", "KZN", "NSK")],
                [("Свободно", [173, 162, 151, 178]),
                 ("В аренде", [25, 22, 16, 15]),
                 ("Обслуживание", [5, 9, 9, 8]),
                 ("Списано", [0, 1, 0, 1])],
                xlabel="Филиал", ylabel="Количество, единиц",
                note="Источник: запрос 2 (v_branch_load)")

    pie("chart_02_categories.svg",
        "Структура парка техники по категориям",
        ["Компьютерная техника", "Лабораторное оборудование",
         "Проекционное оборудование", "Сетевое оборудование",
         "Аудио- и видеооборудование", "VR/AR-оборудование",
         "Оргтехника и печать"],
        [289, 115, 109, 87, 83, 50, 42])

    bar_h("chart_03_top_models.svg",
          "Топ-10 моделей техники по числу выдач",
          ["Lenovo ThinkPad E14 Gen5", "Ubiquiti UniFi 6 Pro", "MikroTik RB4011",
           "Cisco Catalyst 2960-X", "Dell Latitude 5540", "Rigol DP832",
           "SMART SB680", "Keysight DSOX1204G", "Thermo Evolution 201", "Leica DM500"],
          [27, 27, 27, 25, 23, 21, 21, 20, 20, 19],
          xlabel="Число выдач, раз",
          note="Источник: запрос 5")

    bar_v("chart_04_revenue.svg",
          "Поступления платежей по филиалам",
          [branch_label(b) for b in ("HQ", "SPB", "KZN", "NSK")],
          [3765444, 2956980, 2262984, 2159652],
          xlabel="Филиал", ylabel="Сумма, ₽",
          color=SERIES[0],
          note="Источник: запрос 6. Коды филиалов: HQ — Москва, SPB — Санкт-Петербург, "
               "KZN — Казань, NSK — Новосибирск.")

    line_chart("chart_05_revenue_months.svg",
               "Динамика поступлений по месяцам",
               ["12/25", "01/26", "02/26", "03/26", "04/26", "05/26",
                "06/26", "07/26", "08/26", "09/26", "10/26"],
               [989806, 464702, 986307, 762477, 988477, 682884,
                1108334, 665160, 1325304, 2537422, 634187],
               xlabel="Месяц", ylabel="Сумма, ₽",
               note="Источник: запрос 7.",
               partial_last=True,
               partial_note="Октябрь 2026 — неполный месяц (данные по 09.10.2026): "
                            "пунктир — предварительные данные")

    bar_h("chart_06_requests_status.svg",
          "Заявки на аренду по статусам",
          ["выполнена", "подана", "согласована", "договор", "отклонена", "отменена"],
          [80, 68, 38, 34, 26, 17],
          xlabel="Количество заявок, шт.",
          note="Источник: запрос 9",
          w=1100, h=540)

    bar_h("chart_07_maintenance.svg",
          "Работы по обслуживанию и ремонту техники",
          ["плановое ТО", "ремонт", "чистка", "диагностика", "списание"],
          [79, 67, 59, 53, 2],
          xlabel="Количество работ, шт.",
          note="Источник: запрос 11. Затраты на ремонт составили 3 000 312 ₽.",
          w=1100, h=520)

    bar_h("chart_08_rental_duration.svg",
          "Средний срок аренды по категориям техники",
          ["Проекционное оборудование", "Лабораторное оборудование",
           "Сетевое оборудование", "Оргтехника и печать",
           "Аудио- и видеооборудование", "Компьютерная техника",
           "VR/AR-оборудование"],
          [19.1, 17.5, 16.6, 16.2, 15.9, 15.3, 13.4],
          xlabel="Средний срок аренды, дней",
          note="Источник: запрос 12",
          label_fmt=lambda v: ru(v, 1),
          tick_fmt=lambda v: ru(v, 1))

    bar_v("chart_09_distributed_query.svg",
          "Свободные проекторы Epson EB-X51 (модель 201) по филиалам",
          [branch_label(b) for b in ("NSK", "HQ", "SPB", "KZN")],
          [9, 8, 5, 3],
          xlabel="Филиал", ylabel="Свободно, шт.",
          note="Источник: запрос 15 — распределённый поиск по фрагментам узлов. "
               "HQ — Москва, SPB — Санкт-Петербург, KZN — Казань, NSK — Новосибирск.")

    print("Графики созданы в", OUT)
