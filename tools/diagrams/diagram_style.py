#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The shared house style for every generated diagram and chart.

Any team, any document: assessments, design reviews, analyses of alternatives, call paths, log-event
timelines, code walkthroughs, slide decks and posters. The how-to is the `generated-diagrams` skill
(skills/generated-diagrams/SKILL.md); this file is the code it relies on.

Import it rather than copying the colours into your own script, so a change here reaches every
picture:

    import os, sys
    REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * N))   # N hops to the repo root
    sys.path.insert(0, os.path.join(REPO, "tools", "diagrams"))
    from diagram_style import INK, GREY, font, box, arrow

Colour rules:
  * cyan / yellow / magenta only - never red and green as the only signal (protanopia).
  * every coloured element also carries a LETTER, a NUMBER or a SHAPE, so the picture survives
    greyscale printing and colour-vision deficiency (Section 508).

Prove the key colours: python check_contrast.py
Check arrows land on boxes: python check_arrows.py path/to/build_script.py
"""
import os

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

# ---------------------------------------------------------------- palette
INK = "#1A1F29"     # body text
GREY = "#4E586B"    # secondary text
HAIR = "#C6CCD6"    # hairlines, panel outlines
PAPER = "#FFFFFF"
PANEL = "#FAFBFC"   # legend / note panels

# service boxes
SVC_F, SVC_E = "#FFFFFF", "#4E586B"          # a service with no work in this epic
TOUCH_F, TOUCH_E = "#CCE7EC", "#0A4653"      # cyan  - a service this epic changes
STORE_F, STORE_E = "#EFF1F4", "#4E586B"      # database / bucket / external system

# call-outs
BOTTLE_F, BOTTLE_E = "#F5EFC8", "#5C5011"    # yellow  - a bottleneck (queue, pool, client)
STORY_F, STORY_E = "#F3D9FF", "#7A1FA0"      # magenta - a story and what it needs

# arrows
FLOW = "#4E586B"       # a normal call
SLOW = "#5C5011"       # a call that is where the waiting happens


# ---------------------------------------------------------------- ticket key colours
# EVERY ticket letter gets its own colour, so a key can be picked out by eye.
#
# Section 508: colour is NEVER the only signal. Each circle carries its LETTER, and the letter is
# what identifies the ticket, so the pictures work in greyscale and for colour-vision deficiency of
# any type. The colours are generated rather than picked by hand: one hue per letter, evenly spaced
# around the wheel, each drawn as a LIGHT fill with a DARK ink of the same hue. That keeps every
# pair well above the WCAG AA 4.5:1 text-contrast floor - run `python check_contrast.py` to prove it.
# Because the hues run in letter order, A-Q also reads as a sequence rather than a jumble.
import colorsys

KEY_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXY"
# hue is rotated slightly so A does not land on pure red and the sequence starts in the cyan range
_HUE0, _SPREAD = 0.52, 1.0


def _hex(r, g, b):
    return "#%02X%02X%02X" % (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def _pair(i, n):
    h = (_HUE0 + _SPREAD * i / float(n)) % 1.0
    fill = _hex(*colorsys.hls_to_rgb(h, 0.90, 0.62))
    ink = _hex(*colorsys.hls_to_rgb(h, 0.24, 0.72))
    return fill, ink


KEY_COLOURS = {L: _pair(i, len(KEY_LETTERS)) for i, L in enumerate(KEY_LETTERS)}


def key_colours(letter):
    """Fill and ink for a ticket key circle. An unknown letter falls back to a neutral slate."""
    return KEY_COLOURS.get(letter, ("#E3E7EC", "#26374A"))


def emoji_font(sz):
    """Segoe UI Emoji renders in colour with draw.text(..., embedded_color=True). If it is missing
    (non-Windows), the caller falls back to the text label alone - the pattern name is always
    written out, so no meaning is carried by the emoji by itself (Section 508)."""
    for pth in (r"C:\Windows\Fonts\seguiemj.ttf",):
        try:
            return ImageFont.truetype(pth, sz)
        except Exception:
            pass
    return None


def font(sz, bold=False):
    names = [r"C:\Windows\Fonts\segoeuib.ttf"] if bold else [r"C:\Windows\Fonts\segoeui.ttf"]
    names += [r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"]
    for p in names:
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


F_TITLE = font(34, True)
F_SUB = font(17)
F_SVC = font(16, True)
F_SVCSUB = font(12)
F_TAG = font(12, True)
F_CALL = font(15)
F_CALLH = font(15, True)
F_EDGE = font(14)
F_LEG = font(15)
F_NOTE = font(13)


def wrap(draw, text, fnt, width):
    """Greedy word wrap to a pixel width. Returns a list of lines."""
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def text_block(draw, x, y, text, fnt, width, fill=INK, leading=None):
    """Draw wrapped text at x,y. Returns the y below the last line."""
    lead = leading or (fnt.size + 4)
    for ln in wrap(draw, text, fnt, width):
        draw.text((x, y), ln, fill=fill, font=fnt, anchor="la")
        y += lead
    return y


def box(draw, x, y, w, h, title, sub=None, fill=SVC_F, edge=SVC_E, tag=None, width=2):
    """A service box. `tag` is the short letter code shown top-right (e.g. 'C' for changed)."""
    draw.rounded_rectangle([x, y, x + w, y + h], 8, fill=fill, outline=edge, width=width)
    cx = x + w / 2
    ty = y + (h / 2 - 9 if sub else h / 2)
    draw.text((cx, ty), title, fill=INK, font=F_SVC, anchor="mm")
    if sub:
        draw.text((cx, ty + 18), sub, fill=GREY, font=F_SVCSUB, anchor="mm")
    if tag:
        draw.rounded_rectangle([x + w - 26, y + 6, x + w - 6, y + 24], 4, fill=edge)
        draw.text((x + w - 16, y + 15), tag, fill="#FFFFFF", font=F_TAG, anchor="mm")
    return (x, y, x + w, y + h)


def store(draw, x, y, w, h, title, sub=None):
    """A database / bucket / external system: square corners, so shape alone tells it apart."""
    draw.rectangle([x, y, x + w, y + h], fill=STORE_F, outline=STORE_E, width=2)
    cx = x + w / 2
    # spacing follows the font size, so a diagram that enlarges F_SVC still lays out correctly
    lift = round(F_SVC.size * 0.57)
    gap = round(F_SVC.size * 1.13)
    ty = y + (h / 2 - lift if sub else h / 2)
    draw.text((cx, ty), title, fill=INK, font=F_SVC, anchor="mm")
    if sub:
        draw.text((cx, ty + gap), sub, fill=GREY, font=F_SVCSUB, anchor="mm")
    return (x, y, x + w, y + h)


def arrow(draw, p1, p2, label=None, colour=FLOW, width=2, dash=False, label_above=True):
    """A straight call arrow with an optional label."""
    x1, y1 = p1
    x2, y2 = p2
    if dash:
        n = max(2, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / 12))
        for i in range(n):
            if i % 2:
                continue
            ax = x1 + (x2 - x1) * i / n
            ay = y1 + (y2 - y1) * i / n
            bx = x1 + (x2 - x1) * (i + 1) / n
            by = y1 + (y2 - y1) * (i + 1) / n
            draw.line([ax, ay, bx, by], fill=colour, width=width)
    else:
        draw.line([x1, y1, x2, y2], fill=colour, width=width)
    # head
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (-0.5, 0.5):
        draw.line([x2, y2, x2 - 12 * math.cos(ang + s), y2 - 12 * math.sin(ang + s)],
                  fill=colour, width=width)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        draw.text((mx, my - 10 if label_above else my + 10), label,
                  fill=colour, font=F_EDGE, anchor="ms" if label_above else "mt")


def callout(draw, x, y, w, kind, heading, lines, anchor_to=None):
    """A call-out card.

    kind 'B' = bottleneck (yellow), kind 'S' = story (magenta). The letter is drawn in the
    corner badge so the card is still classifiable in greyscale.
    """
    fill, edge = (BOTTLE_F, BOTTLE_E) if kind == "B" else (STORY_F, STORY_E)
    # every measurement follows the font size, so a diagram that enlarges F_CALL / F_CALLH still
    # gets a box tall enough for its text instead of spilling out of the bottom edge
    pad = max(10, round(F_CALL.size * 0.7))
    hl = F_CALLH.size + 3          # heading leading
    bl = F_CALL.size + 2           # body leading
    bs = F_TAG.size + 6            # corner badge side
    head_lines = wrap(draw, heading, F_CALLH, w - 2 * pad - bs - 6)
    body_lines = []
    for ln in lines:
        body_lines.extend(wrap(draw, ln, F_CALL, w - 2 * pad))
    h = pad * 2 + len(head_lines) * hl + len(body_lines) * bl + (4 if body_lines else 0)
    draw.rounded_rectangle([x, y, x + w, y + h], 8, fill=fill, outline=edge, width=2)
    draw.rounded_rectangle([x + w - 6 - bs, y + 6, x + w - 6, y + 6 + bs], 4, fill=edge)
    draw.text((x + w - 6 - bs / 2, y + 6 + bs / 2), kind, fill="#FFFFFF", font=F_TAG, anchor="mm")
    ty = y + pad
    for ln in head_lines:
        draw.text((x + pad, ty), ln, fill=edge, font=F_CALLH, anchor="la")
        ty += hl
    if body_lines:
        ty += 4
    for ln in body_lines:
        draw.text((x + pad, ty), ln, fill=INK, font=F_CALL, anchor="la")
        ty += bl
    if anchor_to:
        draw.line([x, y + 18, anchor_to[0], anchor_to[1]], fill=edge, width=1)
    return h


FOOT_MARGIN = 40


def footer_font(width):
    """The footer's font: it grows with the canvas so it stays readable on a slide (26 px at 3200 wide),
    from 22 px on a narrow picture up to 32 px on a poster, so it never outgrows the body text."""
    return font(min(32, max(22, int(width) // 120)))


def footer_height(width, lines=1):
    """Pixels to reserve at the bottom edge for a footer of `lines` lines on a canvas this wide."""
    f = footer_font(width)
    return lines * (f.size + 6) + 14


def footer(draw, width, height, text):
    """The provenance line every generated picture carries along its bottom edge:

        footer(d, W, H, "Generated by tools/.../build_x.py from data/x.csv - do not hand-edit.")

    It is wrapped to the canvas width (less a margin each side) and drawn upwards from the bottom
    edge, in grey. Returns the y of the top of the footer, so the caller can check nothing it drew
    reaches that far down (the slide kit's Slide.footer does this for its key)."""
    f = footer_font(width)
    lines = wrap(draw, text, f, width - 2 * FOOT_MARGIN)
    lead = f.size + 6
    top = height - 14 - lead * len(lines)
    y = top
    for ln in lines:
        draw.text((FOOT_MARGIN, y), ln, fill=GREY, font=f, anchor="la")
        y += lead
    return top


def legend(draw, x, y, w, items):
    """items: list of (kind, text) where kind is 'C' changed, 'B' bottleneck, 'S' story, '' plain."""
    h = 40
    draw.rounded_rectangle([x, y, x + w, y + h], 6, fill=PANEL, outline=HAIR, width=1)
    lx = x + 14
    draw.text((lx, y + h / 2), "LEGEND", fill=GREY, font=F_CALLH, anchor="lm")
    lx += 76
    for kind, txt in items:
        if kind == "C":
            draw.rounded_rectangle([lx, y + 10, lx + 20, y + 30], 4, fill=TOUCH_F, outline=TOUCH_E, width=2)
        elif kind == "B":
            draw.rounded_rectangle([lx, y + 10, lx + 20, y + 30], 4, fill=BOTTLE_F, outline=BOTTLE_E, width=2)
            draw.text((lx + 10, y + 20), "B", fill=BOTTLE_E, font=F_TAG, anchor="mm")
        elif kind == "S":
            draw.rounded_rectangle([lx, y + 10, lx + 20, y + 30], 4, fill=STORY_F, outline=STORY_E, width=2)
            draw.text((lx + 10, y + 20), "S", fill=STORY_E, font=F_TAG, anchor="mm")
        else:
            draw.rectangle([lx, y + 10, lx + 20, y + 30], fill=STORE_F, outline=STORE_E, width=2)
        draw.text((lx + 28, y + 20), txt, fill=INK, font=F_LEG, anchor="lm")
        lx += 28 + draw.textlength(txt, font=F_LEG) + 26
    return h
