#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that the house colours stay tellable-apart for colour-blind readers and in greyscale.

What it reads:
  * the palette in diagram_style.py - the five card colours (fill and edge of SVC, TOUCH, STORE,
    BOTTLE, STORY) and every KEY_COLOURS letter (its light fill and its dark ink);
  * optionally a PNG, which it re-draws as each kind of reader would see it.

What it does:
  * simulates the three kinds of colour blindness - protanopia (no red cones), deuteranopia (no green
    cones), tritanopia (no blue cones) - with the Machado, Oliveira and Fernandes (2009) matrices at
    full strength, plus plain greyscale printing;
  * for each pair of colours that is MEANT to be told apart, measures how different the two still look
    under each simulation, as a CIEDE2000 colour difference (delta E: 0 = identical, about 2 = the
    smallest difference most people notice);
  * a pair "collapses" when its difference falls below the threshold for its kind of pair:
        fill vs fill of two card kinds      at least 6   (large areas side by side)
        edge vs edge of two card kinds      at least 6
        fill vs its own edge or ink         at least 30  (text and outlines on their own fill)
    Two KEY_COLOURS letters are NOT compared with each other: the letter printed in the circle is what
    tells tickets apart, the colour is only a help (see diagram_style.py).
  * a collapse under protanopia, deuteranopia or tritanopia FAILS the run. Two kinds of collapse are
    only warnings, because the house style already makes something else carry the meaning:
        - greyscale: every card fill is the same light tint by design, so in a greyscale print the
          letter, number or shape on the card is what tells kinds apart;
        - any pair with a STORE card: a store has square corners, so shape separates it.
    --strict turns those warnings into failures too.

Run:
    python check_colour_blind.py                       check the palette only
    python check_colour_blind.py diagram.png           also write simulated previews of the picture
    python check_colour_blind.py diagram.png --out DIR previews go to DIR (default: a temp folder)
    python check_colour_blind.py --colours             also print every colour as each reader sees it

With a PNG, only pairs whose two colours both appear in the picture can fail the run; the rest are
still listed. Prints a table; exit status 1 if any pair collapses (see above), else 0.
"""
import argparse
import itertools
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import diagram_style as ds                                         # noqa: E402

THRESHOLD = {"fill vs fill": 6.0, "edge vs edge": 6.0, "fill vs ink": 30.0}

# Machado, Oliveira and Fernandes (2009), severity 1.0, applied to linear RGB
MATRICES = {
    "protanopia": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779),
                   (-0.078411, 0.930809, 0.147602),
                   (0.004733, 0.691367, 0.303900)),
    "greyscale": ((0.2126, 0.7152, 0.0722),) * 3,
}
VIEWS = ["normal"] + list(MATRICES)


# ------------------------------------------------------------------ colour maths
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    c = max(0.0, min(1.0, c))
    return 255.0 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def simulate(rgb, view):
    if view == "normal":
        return tuple(float(v) for v in rgb)
    lin = [_lin(v) for v in rgb]
    m = MATRICES[view]
    return tuple(_gam(sum(m[r][k] * lin[k] for k in range(3))) for r in range(3))


def lab(rgb):
    r, g, b = (_lin(v) for v in rgb)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e2000(c1, c2):
    """CIEDE2000 difference between two sRGB colours (0-255 tuples)."""
    L1, a1, b1 = lab(c1)
    L2, a2, b2 = lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dh = 0.0
    elif abs(h2p - h1p) <= 180:
        dh = h2p - h1p
    else:
        dh = h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hm = (h1p + h2p) / 2
    else:
        hm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm))
         + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.20 * math.cos(math.radians(4 * hm - 63)))
    SL = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    SC = 1 + 0.045 * Cmp
    SH = 1 + 0.015 * Cmp * T
    RT = (-2 * math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7))
          * math.sin(math.radians(60 * math.exp(-((hm - 275) / 25) ** 2))))
    return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))


# ------------------------------------------------------------------ the pairs that must stay apart
def palette():
    """name -> hex for every colour in the house palette that carries meaning."""
    cards = {"SVC": (ds.SVC_F, ds.SVC_E), "TOUCH": (ds.TOUCH_F, ds.TOUCH_E), "STORE": (ds.STORE_F, ds.STORE_E),
             "BOTTLE": (ds.BOTTLE_F, ds.BOTTLE_E), "STORY": (ds.STORY_F, ds.STORY_E)}
    return cards, dict(ds.KEY_COLOURS)


def pairs():
    """(kind, name a, hex a, name b, hex b, by_shape) for every pair meant to be told apart.
    by_shape is True when the two are ALSO told apart by shape (a store card has square corners),
    so a collapse there is a warning, not a failure."""
    cards, keys = palette()
    out = []
    for (na, (fa, _)), (nb, (fb, _)) in itertools.combinations(cards.items(), 2):
        if fa.upper() != fb.upper():
            out.append(("fill vs fill", na + "_F", fa, nb + "_F", fb, "STORE" in (na, nb)))
    for (na, (_, ea)), (nb, (_, eb)) in itertools.combinations(cards.items(), 2):
        if ea.upper() != eb.upper():                    # SVC and STORE share an edge on purpose
            out.append(("edge vs edge", na + "_E", ea, nb + "_E", eb, "STORE" in (na, nb)))
    for n, (f, e) in cards.items():
        out.append(("fill vs ink", n + "_F", f, n + "_E", e, False))
    for letter, (f, e) in keys.items():
        out.append(("fill vs ink", "key %s fill" % letter, f, "key %s ink" % letter, e, False))
    return out


def colours_in(png):
    """The set of exact colours (upper-case hex) that cover at least 0.01% of the picture."""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    counts = im.getcolors(maxcolors=im.width * im.height) or []
    floor = im.width * im.height * 0.0001
    return {"#%02X%02X%02X" % c for n, c in counts if n >= floor}


def previews(png, out_dir):
    """Write the picture as each reader sees it, side by side, and one file per view."""
    from PIL import Image, ImageDraw
    src = Image.open(png).convert("RGB")
    lin_lut = [_lin(v) for v in range(256)]
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(png))[0]
    views = {"normal": src}
    all_colours = src.getcolors(maxcolors=src.width * src.height)
    for view, m in MATRICES.items():
        # a 3x3 matrix on linear RGB: decode to linear, mix, re-encode. Done on the distinct colours
        # only, which a flat diagram has few of, so it stays fast without numpy.
        table = {}
        for _, c in all_colours:
            lin = [lin_lut[v] for v in c]
            table[c] = tuple(int(round(_gam(sum(m[r][k] * lin[k] for k in range(3))))) for r in range(3))
        im = Image.new("RGB", src.size)
        flat = src.get_flattened_data() if hasattr(src, "get_flattened_data") else src.getdata()
        im.putdata([table[tuple(c)] for c in flat])
        views[view] = im
    written = []
    for view, im in views.items():
        if view == "normal":
            continue
        p = os.path.join(out_dir, "%s.%s.png" % (base, view))
        im.save(p)
        written.append(p)
    # the side-by-side sheet: each view scaled to 800 wide, labelled
    tw = 800
    th = round(src.height * tw / src.width)
    sheet = Image.new("RGB", (tw * 3 + 40, (th + 50) * 2 + 20), "#FFFFFF")
    d = ImageDraw.Draw(sheet)
    for i, view in enumerate(VIEWS[:6]):
        cx, cy = 10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 50)
        sheet.paste(views[view].resize((tw, th)), (cx, cy + 40))
        d.text((cx, cy + 4), view, fill=ds.INK, font=ds.font(26, True))
    p = os.path.join(out_dir, "%s.colour-blind.png" % base)
    sheet.save(p)
    return [p] + written


def check(png=None, show_colours=False, strict=False):
    present = colours_in(png) if png else None
    rows, failed, warned = [], 0, 0
    for kind, na, ha, nb, hb, by_shape in pairs():
        a, b = hex_rgb(ha), hex_rgb(hb)
        des = {v: delta_e2000(simulate(a, v), simulate(b, v)) for v in VIEWS}
        low = [v for v in VIEWS if des[v] < THRESHOLD[kind]]
        # greyscale, or a pair a shape also separates: the letter or shape must carry it - a warning
        hard = [v for v in low if v != "greyscale" and not by_shape]
        soft = [v for v in low if v not in hard]
        counts = present is None or (ha.upper() in present and hb.upper() in present)
        if counts and (hard or (strict and soft)):
            failed += 1
        elif counts and soft:
            warned += 1
        if hard or (strict and soft):
            res = "COLLAPSES in " + ", ".join(low)
        elif soft:
            res = "warn: close in %s - %s must carry it" % (", ".join(soft),
                                                          "shape" if by_shape else "the letter or shape")
        else:
            res = "ok"
        if low and not counts:
            res += " (not in this picture)"
        rows.append((kind, na, nb, des, res))

    print("Colour pairs that must stay apart, as CIEDE2000 delta E under each view")
    print("(thresholds: %s)\n" %", ".join("%s >= %g" % kv for kv in THRESHOLD.items()))
    hdr = "%-13s %-34s" % ("pair kind", "colours") + "".join("%13s" % v for v in VIEWS) + "  result"
    print(hdr)
    print("-" * len(hdr))
    for kind, na, nb, des, res in rows:
        print("%-13s %-34s" % (kind, na + " / " + nb) + "".join("%13.1f" % des[v] for v in VIEWS) + "  " + res)

    if show_colours:
        cards, keys = palette()
        print("\nEvery colour as each reader sees it")
        names = [(n + "_F", f) for n, (f, _) in cards.items()] + [(n + "_E", e) for n, (_, e) in cards.items()]
        names += [("key %s %s" % (L, w), c) for L, fe in keys.items() for w, c in zip(("fill", "ink"), fe)]
        for n, h in names:
            print("%-14s" % n + "".join("  %s %s" % (v[:5], "#%02X%02X%02X" % tuple(int(round(x)) for x in
                                                                              simulate(hex_rgb(h), v)))
                                      for v in VIEWS))
    return rows, failed, warned, present


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check the house colours under colour-blindness simulations.")
    ap.add_argument("png", nargs="?", help="a picture to re-draw as each reader sees it")
    ap.add_argument("--out", help="folder for the simulated previews (default: a new temp folder)")
    ap.add_argument("--colours", action="store_true", help="print every colour as each reader sees it")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on greyscale collapses and on pairs a shape already separates")
    a = ap.parse_args(argv)
    rows, failed, warned, present = check(a.png, a.colours, a.strict)
    if a.png:
        used = [n for n, h in [(n + "_" + s, c) for n, fe in palette()[0].items() for s, c in zip("FE", fe)]
                if h.upper() in present]
        print("\nCard colours found in the picture: %s" % (", ".join(used) or "none"))
        out = a.out or tempfile.mkdtemp(prefix="colour-blind-")
        written = previews(a.png, out)
        print("Previews written:\n  " + "\n  ".join(written))
    print("\n%d pairs checked, %d collapse%s, %d warning%s" % (len(rows), failed, "" if failed == 1 else "s",
                                                           warned, "" if warned == 1 else "s"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
