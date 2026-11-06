#!/usr/bin/env python3
"""Generate the Corne cheatsheet PDF (all layers, chords, Karabiner mapping).

    python3 cheatsheet/cheatsheet.py            # -> cheatsheet/Corne-шпаргалка.pdf

Needs reportlab and fontTools (pip install reportlab fonttools) and macOS fonts
(Arial, Arial Unicode). Key geometry comes from config/eyelash_corne.json; the
key labels below are written by hand, so update them together with the keymap
and karabiner/corne.json.
"""
import json, math, sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
LAYOUT_JSON = sys.argv[1] if len(sys.argv) > 1 else str(REPO / "config/eyelash_corne.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else str(HERE / "Corne-шпаргалка.pdf")
try:
    COMMIT = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
except Exception:
    COMMIT = "?"

pdfmetrics.registerFont(TTFont("U", "/Library/Fonts/Arial Unicode.ttf"))
pdfmetrics.registerFont(TTFont("B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("R", "/System/Library/Fonts/Supplemental/Arial.ttf"))

geo = list(json.load(open(LAYOUT_JSON))["layouts"].values())[0]["layout"]

INK = HexColor("#1f2328"); MUTED = HexColor("#6b7280"); LINE = HexColor("#c9ced6")
KIND = {  # fill, border
    "key":   (HexColor("#ffffff"), HexColor("#9aa3ae")),
    "mod":   (HexColor("#e8eefc"), HexColor("#6f8fd8")),
    "layer": (HexColor("#fdecd2"), HexColor("#e09a3a")),
    "mac":   (HexColor("#e3f4e8"), HexColor("#4fa36b")),
    "sys":   (HexColor("#fbe4e4"), HexColor("#d06060")),
    "media": (HexColor("#f0e8fb"), HexColor("#9471cf")),
    "trans": (HexColor("#f6f7f9"), HexColor("#dde1e6")),
    "none":  (HexColor("#eceef1"), HexColor("#dde1e6")),
}

def K(main, hold=None, kind="key"):
    return (main, hold, kind)

T = K("", None, "trans")
N = K("—", None, "none")

# ---------- layers (positions 0..47) ----------
base = [
    K("Tab"), K("Q"), K("W"), K("E"), K("R"), K("T"), K("↑", "джойстик"), K("Y"), K("U"), K("I"), K("O"), K("P"), K("["),
    K("⇧", "2×: Caps", "mod"), K("A"), K("S"), K("D"), K("F"), K("G"),
    K("←", "джойстик"), K("Enter", "нажатие"), K("→", "джойстик"),
    K("H"), K("J"), K("K"), K("L"), K(";"), K("'"),
    K("⌃ Ctrl", None, "mod"), K("Z"), K("X"), K("C"), K("V"), K("B"), None,
    K("↓", "джойстик"), K("N"), K("M"), K(","), K("."), K("/"), K("⌫"),
    K("⌘ Cmd", None, "mod"), K("Язык", "NUM", "layer"), K("Space"),
    K("Enter"), K("Hyper", "AERO", "layer"), K("Esc", "⌥ R", "mod"),
]
num = [
    K("⇧Tab"), K("1"), K("2"), K("3"), K("4"), K("5"), T, K("6"), K("7"), K("8"), K("9"), K("0"), K("\\"),
    T, K("`"), K("[", "Insert", "mac"), K("]", "App", "mac"), K("-"), K("="),
    T, T, T,
    K("←"), K("↓"), K("↑"), K("→"), K("Home"), K("PgUp"),
    T, K("⌘Z", "отмена", "mac"), K("⌘X", "вырезать", "mac"), K("⌘C", "копировать", "mac"), K("⌘V", "вставить", "mac"), K("⌥⌫", "удалить слово", "mac"), None,
    T, K("Del"), K("Vol−", None, "media"), K("Vol+", None, "media"), K("Prev", None, "media"), K("End"), K("PgDn"),
    T, K("держишь", None, "layer"), T,
    K("⌘ Cmd", None, "mod"), K("Hyper", "+ цифра", "layer"), K("FUNC", "держать", "layer"),
]
func = [
    K("Studio", "unlock", "sys"), K("F1"), K("F2"), K("F3"), K("F4"), K("F5"), T, K("F6"), K("F7"), K("F8"), K("F9"), K("F10"), K("F11"),
    T, K("BT 0", None, "sys"), K("BT 1", None, "sys"), K("BT 2", None, "sys"), K("BT 3", None, "sys"), K("BT clr", None, "sys"),
    T, T, T,
    K("USB", None, "sys"), K("BLE", None, "sys"), K("RGB", "вкл/выкл", "media"), K("RGB", "эффект", "media"), K("⌘⇧4", "скрин", "mac"), K("F12"),
    T, K("Reset", None, "sys"), K("Ярк−", "экран", "media"), K("Boot", "прошивка", "sys"), K("Ярк+", "экран", "media"), K("▶/❚❚", None, "media"), None,
    T, K("RGB −", "яркость", "media"), K("RGB +", "яркость", "media"), K("Boot", "прошивка", "sys"), K("Reset", None, "sys"), K("RGB", "белый 50%", "media"), K("Next", None, "media"),
    T, K("держишь", None, "layer"), T,
    T, T, K("держишь", None, "layer"),
]
aero = [T] * 48
aero[34] = None
aero[44] = K("Sol", "⌥R+Space", "mac")
aero[46] = K("держишь", None, "layer")

# ---------- drawing ----------
def rot(px, py, cx, cy, deg):
    a = math.radians(deg)
    dx, dy = px - cx, py - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)

def fit(c, text, font, size, maxw):
    while size > 4 and pdfmetrics.stringWidth(text, font, size) > maxw:
        size -= 0.25
    return size

def draw_board(c, layer, ox, oy, u, title=None, highlight=()):
    # ox, oy = top-left in PDF coords
    if title:
        c.setFont("B", 12); c.setFillColor(INK); c.drawString(ox, oy + 8, title)
    pad = 0.06 * u
    for i, g in enumerate(geo):
        if layer[i] is None:
            continue
        main, hold, kind = layer[i]
        sx, sy = g["x"] + 0.5, g["y"] + 0.5
        r = g.get("r", 0)
        if r:
            sx, sy = rot(sx, sy, g["rx"], g["ry"], r)
        px, py = ox + sx * u, oy - sy * u
        fill, border = KIND[kind]
        c.saveState()
        c.translate(px, py)
        c.rotate(-r)
        w = u - 2 * pad
        c.setFillColor(fill); c.setStrokeColor(border)
        c.setLineWidth(1.6 if i in highlight else 0.7)
        if i in highlight:
            c.setStrokeColor(HexColor("#e03b3b"))
        c.roundRect(-w / 2, -w / 2, w, w, 0.12 * u, stroke=1, fill=1)
        if main:
            c.setFillColor(INK if kind != "none" else MUTED)
            fs = fit(c, main, "U", 0.30 * u if len(main) <= 2 else 0.22 * u, w - 4)
            c.setFont("U", fs)
            y = 0.02 * u if hold else -fs * 0.35
            c.drawCentredString(0, y, main)
        if hold:
            c.setFillColor(MUTED)
            fs = fit(c, hold, "U", 0.15 * u, w - 4)
            c.setFont("U", fs)
            c.drawCentredString(0, -0.30 * u, hold)
        c.restoreState()

def legend(c, x, y):
    items = [("key", "обычная клавиша"), ("mod", "модификатор"), ("layer", "слой / тап+удержание"),
             ("mac", "работает через Karabiner / macOS"), ("media", "медиа, яркость, подсветка"),
             ("sys", "Bluetooth, прошивка, сброс"), ("trans", "прозрачная: как в нижнем слое")]
    c.setFont("U", 8)
    for k, label in items:
        fill, border = KIND[k]
        c.setFillColor(fill); c.setStrokeColor(border); c.setLineWidth(0.7)
        c.roundRect(x, y - 2, 11, 11, 2, fill=1, stroke=1)
        c.setFillColor(INK); c.drawString(x + 15, y + 1, label)
        x += 15 + pdfmetrics.stringWidth(label, "U", 8) + 9

from fontTools.ttLib import TTFont as _FT
_BCMAP = _FT("/System/Library/Fonts/Supplemental/Arial Bold.ttf").getBestCmap()
def bold_for(t):
    return "B" if all(ord(ch) in _BCMAP for ch in t) else "U"

def para(c, x, y, lines, size=9, lead=None, width=None):
    lead = lead or size * 1.35
    for ln in lines:
        if isinstance(ln, tuple):
            head, body = ln
            hf = bold_for(head)
            c.setFont(hf, size); c.setFillColor(INK); c.drawString(x, y, head)
            hw = pdfmetrics.stringWidth(head + " ", hf, size)
            c.setFont("U", size); c.drawString(x + hw, y, body)
        elif ln.startswith("#"):
            y -= size * 0.4
            c.setFont("B", size + 2.5); c.setFillColor(INK); c.drawString(x, y, ln[1:].strip())
            y -= size * 0.35
        else:
            c.setFont("U", size); c.setFillColor(INK); c.drawString(x, y, ln)
        y -= lead
    return y

def header(c, title, sub, page):
    W, H = landscape(A4)
    c.setFillColor(INK); c.setFont("B", 18); c.drawString(30, H - 42, title)
    c.setFont("U", 9); c.setFillColor(MUTED); c.drawString(30, H - 57, sub)
    c.drawRightString(W - 30, H - 42, f"Eyelash Corne · стр. {page}/4")
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(30, H - 65, W - 30, H - 65)

W, H = landscape(A4)
c = canvas.Canvas(OUT, pagesize=landscape(A4))
c.setTitle("Eyelash Corne — шпаргалка"); c.setAuthor("corneSetup")

# ---- page 1: base ----
header(c, "Слой 0 · QWERTY (основной)",
       f"Прошивка ветки mac-aerospace, коммит {COMMIT}. На клавише: сверху — тап, снизу серым — удержание или пояснение.", 1)
u = 46
draw_board(c, base, 30, H - 85, u)
legend(c, 30, H - 85 - 4.75 * u)
y = para(c, 30, H - 85 - 5.25 * u, [
    "# Клавиши с двумя действиями",
    ("Левый FN (Язык / NUM):", "тап — Pause, Karabiner переключает ABC ↔ RussianWin. Удержание — слой NUM."),
    ("", "Режим balanced, 250 мс: слой включается, только если другую клавишу нажали и отпустили, пока FN зажат."),
    ("", "Поэтому можно переключить язык и сразу печатать, не дожидаясь отпускания FN."),
    ("Правый FN (Hyper / AERO):", "держишь — Left Option + слой AERO. Karabiner превращает Left Option в ⌘⌃⌥ (Hyper) для AeroSpace."),
    ("Крайний правый палец (Esc / ⌥R):", "тап — Esc, удержание — Right Option. В Logic Pro и Final Cut Pro удержание — Hyper для AeroSpace."),
    ("Левый Cmd + левый FN вместе:", "чистый Option, пока держишь (одним большим пальцем) — для Option+клика трекпадом."),
    ("⇧ слева:", "тап/удержание — Shift, двойной тап — Caps Lock (Karabiner превращает Caps Lock в Hyper ⌘⌃⌥)."),
    ("Джойстик:", "стрелки, нажатие — Enter."),
], size=10)

# ---- page 2: NUM + FUNC ----
c.showPage()
header(c, "Слои 1–2 · NUM+SYM и Fn",
       "NUM — держишь левый FN.  Fn — держишь левый FN, потом крайний правый палец.", 2)
u = 38
draw_board(c, num, 30, H - 92, u, title="Слой 1 · NUM+SYM  (держишь левый FN)", highlight=(43,))
draw_board(c, func, 30, H - 92 - 5.05 * u, u, title="Слой 2 · Fn  (левый FN + крайний правый палец)", highlight=(43, 47))
xr = 30 + 17.9 * u
para(c, xr, H - 100, [
    "# Важно",
    "[ и ] (FN+S, FN+D)",
    "отправляют Insert / App,",
    "Karabiner ставит скобки.",
    "В Obsidian работают и в",
    "русской раскладке.",
    "В других приложениях в RU",
    "это «х» и «ъ».",
    "",
    "` в русской раскладке — «ё».",
    "",
    "Правый Enter в NUM — ⌘ Cmd:",
    "FN + Enter + цифра/стрелка.",
    "Правый FN в NUM — Hyper:",
    "оба FN + цифра = AeroSpace",
    "(в любом порядке нажатия).",
    "Слово влево/вправо — аккорды",
    "FN + F+D / FN + J+K.",
    "",
    "# Fn-слой",
    "BT 0–3 — профили Bluetooth",
    "BT clr — забыть текущий",
    "USB / BLE — куда слать",
    "Boot — режим прошивки",
    "  (появится диск, кинь .uf2)",
    "Reset — перезагрузка",
    "⌘⇧4 — скриншот области",
    "Studio unlock — для",
    "  ZMK Studio (по USB)",
], size=8.5)

# ---- page 3: AERO + combos ----
c.showPage()
header(c, "Слой 3 · AERO и аккорды",
       "AERO включается, пока держишь правый FN. Всё прозрачное: AeroSpace получает Hyper + клавишу.", 3)
u = 38
draw_board(c, aero, 30, H - 92, u, title="Слой 3 · AERO  (держишь правый FN)", highlight=(46,))
xr = 30 + 17.9 * u
para(c, xr, H - 100, [
    "# Как работает",
    "Правый FN держит Left Option.",
    "Karabiner делает из него",
    "⌘⌃⌥ (кроме Logic Pro и",
    "Final Cut Pro).",
    "Правый FN + любая клавиша",
    "= Hyper + клавиша",
    "→ AeroSpace.",
    "",
    "Правый FN + Space (левый",
    "большой палец) — Sol:",
    "Option отпускается, уходит",
    "Keypad = (Karabiner →",
    "⌥R+Space), потом Option",
    "зажимается снова.",
], size=8.5)

combo_y = H - 92 - 4.9 * u
c.setFont("B", 12); c.setFillColor(INK); c.drawString(30, combo_y, "Аккорды (нажать одновременно)")
rows = [
    ("A S D F", ".", "все 4 за 60 мс; не срабатывает в первые 150 мс после печати. Точка в ABC и в RU"),
    ("J K L ;", ",", "то же самое, запятая в ABC и в RU"),
    ("все 6 больших пальцев", "заблокировать Mac", "⌃⌘Q; за 80 мс, не срабатывает в первые 150 мс после печати"),
    ("левый FN + F D", "⌥ ←", "держишь левый FN и жмёшь F+D вместе — слово влево (с Shift — выделение)"),
    ("левый FN + J K", "⌥ →", "то же, слово вправо"),
    ("левый Cmd + левый FN", "Option", "держишь — чистый Option в любом приложении, для Option+клика"),
    ("Q + S + Z", "выключить", "держать 2 секунды (soft off)"),
]
yy = combo_y - 20
for keys, what, note in rows:
    c.setFillColor(KIND["layer"][0]); c.setStrokeColor(KIND["layer"][1])
    c.roundRect(30, yy - 5, 150, 17, 3, fill=1, stroke=1)
    c.setFillColor(INK); c.setFont("B", 9); c.drawString(37, yy, keys)
    c.setFont(bold_for(what), 16 if len(what) == 1 else 10); c.drawString(192, yy - (2 if len(what) == 1 else 0), what)
    c.setFont("U", 8.5); c.setFillColor(MUTED); c.drawString(300, yy, note)
    yy -= 24
c.setFont("U", 8.5); c.setFillColor(MUTED)
c.drawString(30, yy, "Аккорды asdf / jkl; работают только в слое QWERTY. Порядок нажатия не важен.")

# ---- page 4: Karabiner + timings ----
c.showPage()
header(c, "Mac: Karabiner и тайминги",
       "Часть клавиш шлёт Pause, Scroll Lock и т.п., а символ ставит Karabiner (~/.config/karabiner/karabiner.json, правила «Corne: …»).", 4)
rows = [
    ("Pause", "тап левого FN", "RussianWin → ABC, иначе → RussianWin"),
    ("Scroll Lock", "аккорд J K L ;", "ABC: «,»   ·   RussianWin: ⇧/ («,»)"),
    ("Print Screen", "аккорд A S D F", "ABC: «.»   ·   RussianWin: / («.»)"),
    ("Insert", "левый FN + S", "«[». В Obsidian при RU: на миг ABC → [ → обратно RU"),
    ("Application", "левый FN + D", "«]». В Obsidian при RU: на миг ABC → ] → обратно RU"),
    ("Left Option", "правый FN", "⌘⌃⌥ Hyper (кроме Logic Pro и Final Cut Pro — там Option)"),
    ("Right Option", "удержание Esc", "в Logic Pro / Final Cut Pro — ⌘⌃⌥ Hyper (AeroSpace)"),
    ("Keypad =", "правый FN + Space", "⌥R + Space → Sol (работает и в Logic)"),
    ("Keypad 0", "левый Cmd + левый FN", "чистый Left Option, без Hyper"),
    ("Keypad 1", "левый FN + B", "⌥⌫ — удалить слово"),
    ("Keypad 2 / 3", "левый FN + F D / J K", "⌥← / ⌥→ — прыжок по словам"),
    ("Caps Lock", "двойной тап ⇧", "⌘⌃⌥ Hyper"),
]
y = H - 95
c.setFont("B", 9.5); c.setFillColor(MUTED)
for x, t in ((30, "Клавиша"), (140, "Откуда"), (330, "Что делает Karabiner")):
    c.drawString(x, y, t)
y -= 6; c.setStrokeColor(LINE); c.line(30, y, W - 30, y); y -= 16
for k, src, what in rows:
    c.setFillColor(INK); c.setFont(bold_for(k), 10); c.drawString(30, y, k)
    c.setFont("U", 9.5); c.drawString(140, y, src); c.drawString(330, y, what)
    y -= 8; c.setStrokeColor(HexColor("#eef0f3")); c.line(30, y, W - 30, y); y -= 14

y -= 8
y = para(c, 30, y, [
    "# Тайминги прошивки",
    ("Левый FN:", "balanced, 250 мс до удержания, повторный тап в течение 150 мс — повтор тапа."),
    ("Esc / ⌥R:", "hold-preferred, 200 мс; тап и сразу удержание в течение 200 мс — автоповтор Esc."),
    ("Debounce:", "8 мс на нажатие и отпускание.   NKRO включён — не выключать: macOS перестаёт понимать клавиатуру."),
    ("Сон:", "через 1 час простоя; подсветка гаснет при простое."),
    "# Если что-то не так",
    ("Язык не переключился:", "проверь, что Karabiner запущен и правило «Corne: Pause …» включено."),
    ("Буква повторяется:", "часто из-за AirPods на том же Bluetooth. Увеличь «Задержку перед повтором» в настройках клавиатуры macOS."),
    ("Скобка в Obsidian вышла «х»:", "раскладка не успела переключиться — увеличить паузы hold_down_milliseconds (сейчас 30 мс)."),
], size=9.5)

c.save()
print("saved", OUT)
