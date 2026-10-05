#!/usr/bin/env python3
"""Draw the MF DOOM mask for the right nice!view and emit LVGL 1-bit C art.

Usage: python3 scripts/doom_art.py            -> writes boards/shields/nice_view_doom/widgets/art.c
       python3 scripts/doom_art.py preview.png -> also writes an enlarged preview (screen colours)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

W, H = 68, 140          # upright portrait size of the art area on the screen
S = 8                   # supersampling factor for smooth shapes
FG, BG = 255, 0         # FG = screen foreground colour (text colour), BG = background


def big(pts):
    return [(x * S, y * S) for x, y in pts]


def layer(paint):
    """Paint on a supersampled canvas and return it at screen size as a set of FG pixels."""
    img = Image.new("L", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)
    paint(d)
    small = img.resize((W, H), Image.BOX)
    return {(x, y) for y in range(H) for x in range(W) if small.getpixel((x, y)) >= 128}


def ell(d, box, fill):
    d.ellipse([c * S for c in box], fill=fill)


def poly(d, pts, fill):
    d.polygon(big(pts), fill=fill)


def cut(d, pts, w):
    d.line(big(pts), fill=BG, width=max(1, int(w * S)), joint="curve")


MASK_OUTLINE = [(14, 43), (54, 43), (54, 62), (50, 78), (44, 90), (40, 84), (34, 82),
                (28, 84), (24, 90), (18, 78), (14, 62)]


def silhouette(d):
    ell(d, (14, 22, 54, 64), FG)
    poly(d, MASK_OUTLINE, FG)


def mask_details(d):
    silhouette(d)
    # brow ridge
    cut(d, [(16, 44), (26, 47), (34, 45), (42, 47), (52, 44)], 1.6)
    # eye holes (slanted, menacing)
    poly(d, [(17, 49), (29, 51.5), (30, 57), (24, 58.5), (18, 55)], BG)
    poly(d, [(51, 49), (39, 51.5), (38, 57), (44, 58.5), (50, 55)], BG)
    # nose guard ridge and nostrils
    cut(d, [(31.5, 47), (31, 70), (29, 74)], 1.2)
    cut(d, [(36.5, 47), (37, 70), (39, 74)], 1.2)
    ell(d, (29.5, 73.5, 32.5, 76.5), BG)
    ell(d, (35.5, 73.5, 38.5, 76.5), BG)
    # cheek seams
    cut(d, [(15, 60), (22, 70), (26, 80)], 1.2)
    cut(d, [(53, 60), (46, 70), (42, 80)], 1.2)
    # forehead plate seam
    cut(d, [(20, 38), (27, 34), (34, 33), (41, 34), (48, 38)], 1.0)
    # rivets
    for x, y in [(19, 30), (34, 26.5), (49, 30), (17, 66), (51, 66), (22, 83), (46, 83)]:
        ell(d, (x - 1.1, y - 1.1, x + 1.1, y + 1.1), BG)


def hood(d):
    ell(d, (2, 6, 66, 106), FG)
    ell(d, (10, 17, 58, 122), BG)


def lips(d):
    poly(d, [(27, 92), (31, 89.5), (34, 90.5), (37, 89.5), (41, 92), (37, 95.5), (31, 95.5)], FG)
    cut(d, [(27.5, 92.4), (34, 93), (40.5, 92.4)], 0.9)


FONT = {
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    " ": ["000"] * 7,
}


def draw_mask():
    out = Image.new("L", (W, H), BG)
    px = out.putpixel

    near = lambda pts, x, y: any((x + dx, y + dy) not in pts
                                 for dx in (-1, 0, 1) for dy in (-1, 0, 1))

    # hood: solid rim, cloth as a 50% dither so it reads as grey
    hood_px = layer(hood)
    for x, y in hood_px:
        if near(hood_px, x, y) or (x + y) % 2 == 0:
            px((x, y), FG)

    # mask: clear a 1px dark gap around it, then paint the solid metal with its details
    sil = layer(silhouette)
    for x, y in sil:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    px((x + dx, y + dy), BG)
    for x, y in layer(mask_details):
        px((x, y), FG)

    # lips, then the beard as a dither that thickens towards the chin
    for x, y in layer(lips):
        px((x, y), FG)
    for y in range(97, 119):
        for x in range(16, 52):
            if ((x - 34) / 18) ** 2 + ((y - 90) / 28) ** 2 > 1:
                continue
            dense = y > 106
            if (x + y) % 2 == 0 and (dense or y % 2 == 0):
                px((x, y), FG)

    # "MF DOOM" lettering
    text = "MF DOOM"
    width = sum(len(FONT[c][0]) + 1 for c in text) - 1
    x0, y0 = (W - width) // 2, 128
    for c in text:
        for dy, row in enumerate(FONT[c]):
            for dx, bit in enumerate(row):
                if bit == "1":
                    px((x0 + dx, y0 + dy), FG)
        x0 += len(FONT[c][0]) + 1
    return out


def to_c(img):
    # The art is stored rotated: screen up = +x of the 140x68 buffer.
    land = img.rotate(-90, expand=True)
    w, h = land.size
    assert (w, h) == (140, 68)
    stride = (w + 7) // 8
    data = []
    for y in range(h):
        for bx in range(stride):
            byte = 0
            for bit in range(8):
                x = bx * 8 + bit
                # bit 1 = palette index 1 = background, like the stock art
                on = x < w and land.getpixel((x, y)) == BG
                byte |= (1 if on else 0) << (7 - bit)
            data.append(byte)
    rows = [", ".join(f"0x{b:02x}" for b in data[i:i + 15]) for i in range(0, len(data), 15)]
    body = ",\n        ".join(rows)
    return f"""/*
 * MF DOOM mask for the nice!view peripheral screen.
 * Generated by scripts/doom_art.py - edit the script, not this file.
 * SPDX-License-Identifier: MIT
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST uint8_t doom_map[] = {{
#if CONFIG_NICE_VIEW_DOOM_WIDGET_INVERTED
        0xff, 0xff, 0xff, 0xff, /*Color of index 0*/
        0x00, 0x00, 0x00, 0xff, /*Color of index 1*/
#else
        0x00, 0x00, 0x00, 0xff, /*Color of index 0*/
        0xff, 0xff, 0xff, 0xff, /*Color of index 1*/
#endif

        {body},
}};

const lv_img_dsc_t doom = {{
    .header.cf = LV_IMG_CF_INDEXED_1BIT,
    .header.always_zero = 0,
    .header.reserved = 0,
    .header.w = 140,
    .header.h = 68,
    .data_size = {len(data) + 8},
    .data = doom_map,
}};
"""


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    art = draw_mask()
    out = root / "boards/shields/nice_view_doom/widgets/art.c"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_c(art))
    if len(sys.argv) > 1:
        # Preview in the colours seen on the keyboard: light drawing on a dark screen.
        prev = art.point(lambda v: 225 if v else 25).resize((W * 5, H * 5), Image.NEAREST)
        prev.save(sys.argv[1])
    print("wrote", out)
