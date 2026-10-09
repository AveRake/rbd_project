#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CampusRent — генератор графиков по результатам запросов (SVG → PNG).

Графики используются в итоговом отчёте и презентации.
Запуск:  python3 tools/gen_charts.py
Затем:   rsvg-convert -w <px> file.svg -o file.png
"""

import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "graphs")

FONT = "Helvetica, Arial, sans-serif"
TXT = "#111111"
GRID = "#d9d9d9"
SERIES = ["#1f4e79", "#2e75b6", "#9dc3e6", "#c9c9c9", "#8faadc", "#44546a", "#bdd7ee"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
        self.text(40, 42, self.title, size=20, anchor="start", weight="bold")

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="100%" height="100%" fill="#ffffff"/>')
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(head + "\n" + "\n".join(self.p) + "\n</svg>\n")


def fmt(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f} млн"
    if v >= 1000:
        return f"{v/1000:.0f} тыс"
    return f"{v:g}"


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


# ---------------------------------------------------------------------
def bar_v(name, title, cats, values, unit="", color=None, w=1100, h=600, label_fmt=fmt):
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 110, 40, 90, 110
    pw, ph = w - L - R, h - T - B
    vmax = nice_max(max(values))
    # сетка
    for i in range(6):
        y = T + ph - ph * i / 5
        c.line(L, y, L + pw, y)
        c.text(L - 12, y + 5, label_fmt(vmax * i / 5), size=12, anchor="end")
    bw = pw / len(cats)
    for i, (cat, v) in enumerate(zip(cats, values)):
        bh = ph * v / vmax
        x = L + i * bw + bw * 0.18
        c.rect(x, T + ph - bh, bw * 0.64, bh, color or SERIES[i % len(SERIES)])
        c.text(L + i * bw + bw / 2, T + ph - bh - 10, label_fmt(v), size=13, weight="bold")
        # подпись категории (перенос по словам, явные переносы сохраняются)
        for k, ln in enumerate(wrap_lines(cat)):
            c.text(L + i * bw + bw / 2, T + ph + 26 + k * 16, ln, size=12)
    if unit:
        c.text(L, h - 26, unit, size=12, anchor="start", fill="#555555")
    c.save(name)


def bar_h(name, title, cats, values, unit="", color=None, w=1100, h=640, label_fmt=fmt):
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 330, 90, 90, 60
    pw, ph = w - L - R, h - T - B
    vmax = nice_max(max(values))
    rh = ph / len(cats)
    for i, (cat, v) in enumerate(zip(cats, values)):
        y = T + i * rh
        c.rect(L, y + rh * 0.16, pw * v / vmax, rh * 0.62, color or SERIES[i % len(SERIES)])
        c.text(L - 12, y + rh * 0.55, cat, size=13, anchor="end")
        c.text(L + pw * v / vmax + 12, y + rh * 0.55, label_fmt(v), size=13,
               anchor="start", weight="bold")
    for i in range(6):
        x = L + pw * i / 5
        c.line(x, T, x, T + ph, stroke=GRID)
        c.text(x, T + ph + 24, label_fmt(vmax * i / 5), size=12)
    if unit:
        c.text(L, h - 20, unit, size=12, anchor="start", fill="#555555")
    c.save(name)


def bar_stacked(name, title, cats, series, unit="", w=1100, h=600):
    """series: list of (name, values)."""
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 110, 260, 90, 110
    pw, ph = w - L - R, h - T - B
    totals = [sum(s[1][i] for s in series) for i in range(len(cats))]
    vmax = nice_max(max(totals))
    for i in range(6):
        y = T + ph - ph * i / 5
        c.line(L, y, L + pw, y)
        c.text(L - 12, y + 5, f"{vmax*i/5:.0f}", size=12, anchor="end")
    bw = pw / len(cats)
    for i, cat in enumerate(cats):
        acc = 0
        for k, (sname, vals) in enumerate(series):
            bh = ph * vals[i] / vmax
            c.rect(L + i * bw + bw * 0.2, T + ph - acc - bh, bw * 0.6, bh, SERIES[k])
            acc += bh
        c.text(L + i * bw + bw / 2, T + ph - acc - 10, f"{totals[i]:.0f}", size=13, weight="bold")
        for k, ln in enumerate(wrap_lines(cat, 16)):
            c.text(L + i * bw + bw / 2, T + ph + 26 + k * 16, ln, size=13)
    # легенда
    for k, (sname, _vals) in enumerate(series):
        y = T + 10 + k * 28
        c.rect(L + pw + 40, y, 20, 16, SERIES[k])
        c.text(L + pw + 70, y + 13, sname, size=13, anchor="start")
    if unit:
        c.text(L, h - 26, unit, size=12, anchor="start", fill="#555555")
    c.save(name)


def pie(name, title, cats, values, w=980, h=640):
    c = Chart(w, h, title)
    c.header()
    cx, cy, r = 330, 350, 190
    total = sum(values)
    ang = -90
    for i, (cat, v) in enumerate(zip(cats, values)):
        a = 360 * v / total
        a1, a2 = math.radians(ang), math.radians(ang + a)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        large = 1 if a > 180 else 0
        c.path(f"M {cx} {cy} L {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} Z",
               SERIES[i % len(SERIES)])
        mid = math.radians(ang + a / 2)
        lx, ly = cx + r * 0.66 * math.cos(mid), cy + r * 0.66 * math.sin(mid)
        if v / total > 0.06:
            c.text(lx, ly + 5, f"{100*v/total:.0f}%", size=14, weight="bold", fill="#ffffff")
        ang += a
    # легенда
    for i, (cat, v) in enumerate(zip(cats, values)):
        y = 150 + i * 34
        c.rect(600, y, 22, 18, SERIES[i % len(SERIES)])
        c.text(634, y + 14, f"{cat} — {v} ({100*v/total:.1f}%)", size=13, anchor="start")
    c.text(40, h - 24, "Всего: %d экз." % total, size=13, anchor="start", fill="#555555")
    c.save(name)


def line_chart(name, title, cats, values, unit="", w=1200, h=560):
    c = Chart(w, h, title)
    c.header()
    L, R, T, B = 120, 60, 90, 110
    pw, ph = w - L - R, h - T - B
    vmax = nice_max(max(values))
    for i in range(6):
        y = T + ph - ph * i / 5
        c.line(L, y, L + pw, y)
        c.text(L - 12, y + 5, fmt(vmax * i / 5), size=12, anchor="end")
    step = pw / (len(cats) - 1)
    pts = [(L + i * step, T + ph - ph * v / vmax) for i, v in enumerate(values)]
    c.add(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" '
          f'fill="none" stroke="{SERIES[0]}" stroke-width="3"/>')
    for (x, y), v in zip(pts, values):
        c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{SERIES[0]}"/>')
        c.text(x, y - 14, fmt(v), size=12, weight="bold")
    for i, cat in enumerate(cats):
        c.text(L + i * step, T + ph + 28, cat, size=12, rotate=-30)
    if unit:
        c.text(L, h - 20, unit, size=12, anchor="start", fill="#555555")
    c.save(name)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    bar_stacked("chart_01_fleet_load.svg",
                "Загрузка парка техники по филиалам, единиц",
                ["HQ\nМосква", "SPB\nСанкт-Петербург", "KZN\nКазань", "NSK\nНовосибирск"],
                [("Свободно", [173, 162, 151, 178]),
                 ("В аренде", [25, 22, 16, 15]),
                 ("Обслуживание", [5, 9, 9, 8]),
                 ("Списано", [0, 1, 0, 1])],
                unit="Источник: запрос 2 (v_branch_load)")

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
          unit="Источник: запрос 5")

    bar_v("chart_04_revenue.svg",
          "Поступления платежей по филиалам",
          ["HQ", "SPB", "KZN", "NSK"],
          [3765444, 2956980, 2262984, 2159652],
          unit="Источник: запрос 6, руб.",
          label_fmt=fmt)

    line_chart("chart_05_revenue_months.svg",
               "Динамика поступлений по месяцам",
               ["12/25", "01/26", "02/26", "03/26", "04/26", "05/26",
                "06/26", "07/26", "08/26", "09/26", "10/26"],
               [989806, 464702, 986307, 762477, 988477, 682884,
                1108334, 665160, 1325304, 2537422, 634187],
               unit="Источник: запрос 7, руб.")

    bar_h("chart_06_requests_status.svg",
          "Заявки на аренду по статусам",
          ["выполнена", "подана", "согласована", "договор", "отклонена", "отменена"],
          [80, 68, 38, 34, 26, 17],
          unit="Источник: запрос 9",
          w=1100, h=520)

    bar_h("chart_07_maintenance.svg",
          "Работы по обслуживанию и ремонту техники",
          ["плановое ТО", "ремонт", "чистка", "диагностика", "списание"],
          [79, 67, 59, 53, 2],
          unit="Источник: запрос 11. Затраты на ремонт составили 3 000 312 руб.",
          w=1100, h=500)

    bar_h("chart_08_rental_duration.svg",
          "Средний срок аренды по категориям техники",
          ["Проекционное оборудование", "Лабораторное оборудование",
           "Сетевое оборудование", "Оргтехника и печать",
           "Аудио- и видеооборудование", "Компьютерная техника",
           "VR/AR-оборудование"],
          [19.1, 17.5, 16.6, 16.2, 15.9, 15.3, 13.4],
          unit="Источник: запрос 12, дней",
          label_fmt=lambda v: f"{v:.1f}")

    bar_v("chart_09_distributed_query.svg",
          "Свободные проекторы Epson EB-X51 (модель 201) по филиалам",
          ["NSK\nНовосибирск", "HQ\nМосква", "SPB\nСанкт-Петербург", "KZN\nКазань"],
          [9, 8, 5, 3],
          unit="Источник: запрос 15 — распределённый поиск по фрагментам узлов")

    print("Графики созданы в", OUT)
