#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write Section 508 alt text for a generated diagram: a short alt and a long description.

A picture in a document needs two pieces of text for a reader who cannot see it:
  * a SHORT alt (under 150 characters) - what the picture is and what it shows;
  * a LONG description - the parts, then every numbered step in order, in plain sentences.

As a library, from a build script:

    from write_alt_text import alt_text, write_alt
    alt = alt_text("How an order is placed", parts=["Phone app", "Order API"],
                   steps=["The phone app sends the order to the Order API", "..."],
                   finding="The app gets an answer within 2 seconds")
    alt["short"], alt["long"]                     # two strings
    write_alt("assets/architecture.png", alt)     # writes assets/architecture.png.alt.md

    alt = from_slide(s)                           # or straight from a slide_kit Slide, before s.save()

As a command, for a build script that uses slide_kit's Slide:

    python write_alt_text.py path/to/build_script.py [--write]

It runs the script with Slide recording what is drawn (the title, subtitle, zones, cards, arrows and
the labels beside them) and with Slide.save replaced, so NO picture is written. It prints the alt
text; --write also writes <png>.alt.md next to the PNG the script would have saved.

Each numbered arrow becomes a step: "2. From Take the order to Check the order - check it."
The ends of an arrow are matched to the card they touch; the label is the arrow's own label, or the
free text drawn nearest its numbered marker. Steps run in number order, then lettered steps.
Standard library only (the build script itself needs Pillow).
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHORT_MAX = 150


# ------------------------------------------------------------------ the text itself
def _sentence(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    if not s:
        return ""
    s = s[0].upper() + s[1:]
    return s if s[-1] in ".!?" else s + "."


def _clip(s, n):
    if len(s) <= n:
        return s
    cut = s[:n - 1].rsplit(" ", 1)[0].rstrip(",;:-")
    return cut + "…"


def _join(items):
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def alt_text(title, parts=(), steps=(), finding=None, kind="Diagram", groups=None, others=()):
    """Return {"short": str, "long": str}.

    title    - the picture's title (ideally it states the finding)
    parts    - names of the boxes, in reading order
    steps    - one plain sentence per step, in order; or (mark, sentence) to keep a step's own
               number or letter
    others   - sentences for arrows that carry no step number
    finding  - one sentence: what the picture shows (often the subtitle)
    groups   - optional {group name: [part names]} to describe the parts by area
    """
    title = re.sub(r"\s+", " ", str(title)).strip()
    parts, steps = [p for p in parts if p], [s for s in steps if s]
    count = []
    if parts:
        count.append("%d part%s" % (len(parts), "" if len(parts) == 1 else "s"))
    if steps:
        count.append("%d step%s" % (len(steps), "" if len(steps) == 1 else "s"))
    tail = (", " + " and ".join(count)) if count else ""
    short = "%s: %s%s." % (kind, title.rstrip("."), tail)
    if len(short) > SHORT_MAX:
        short = _clip("%s: %s." % (kind, title.rstrip(".")), SHORT_MAX)

    out = [_sentence("%s: %s" % (kind, title))]
    if finding:
        out.append(_sentence(finding))
    if groups:
        for g, names in groups.items():
            if names:
                out.append(_sentence("%s holds %s" % (g, _join(names))))
    elif parts:
        out.append(_sentence("It shows %s" % _join(parts)))
    if steps:
        out.append("")
        out.append("The steps, in order:")
        out.append("")
        for i, st in enumerate(steps, 1):
            mark, text = st if isinstance(st, (tuple, list)) else (i, st)
            out.append("%s. %s" % (mark, _sentence(text)))
    if others:
        out.append("")
        out.append(_sentence("Other arrows, not numbered: " + "; ".join(o.rstrip(".") for o in others)))
    return {"short": short, "long": "\n".join(out).strip()}


def write_alt(png, alt):
    """Write <png>.alt.md beside the picture. Returns the path written."""
    path = str(png) + ".alt.md"
    body = "# Alt text for %s\n\n**Short alt:** %s\n\n**Long description:**\n\n%s\n" % (
        os.path.basename(str(png)), alt["short"], alt["long"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


# ------------------------------------------------------------------ reading a slide_kit Slide
def _clean(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def _near_box(p, boxes, slack=30):
    """The card whose outline is closest to point p, if it is within slack px."""
    best, bd = None, slack + 1
    for name, (x0, y0, x1, y1) in boxes:
        dx = max(x0 - p[0], 0, p[0] - x1)
        dy = max(y0 - p[1], 0, p[1] - y1)
        d = math.hypot(dx, dy)
        if d < bd:
            best, bd = name, d
    return best


def from_record(rec, finding=None):
    """Alt text from a record: {"title", "subtitle", "zones": [(title, rect)], "cards": [(title, rect)],
    "routes": [{"points", "mark", "label"}], "texts": [((x, y), text)]}."""
    cards = rec.get("cards", [])
    zones = [z for z in rec.get("zones", []) if z[0]]
    used_texts = set()
    steps, others = [], []

    def nearest(r, reach=120):
        """The free label drawn nearest the middle of the arrow's first leg."""
        pts = r["points"]
        mx, my = (pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2
        cand = [(math.hypot(x - mx, y - my), i, t) for i, ((x, y), t) in enumerate(rec.get("texts", []))
                if i not in used_texts and math.hypot(x - mx, y - my) <= reach]
        if not cand:
            return None
        _, i, t = min(cand)
        used_texts.add(i)
        return t

    def describe(r, label):
        pts = r["points"]
        zt = [('the "%s" area' % _clean(n).split(". ")[0].split(" - ")[0], r_) for n, r_ in zones]
        a = _near_box(pts[0], cards) or _near_box(pts[0], zt)
        b = _near_box(pts[-1], cards) or _near_box(pts[-1], zt)
        what = "from %s to %s" % (a or "the start", b or "the end") if (a or b) else "an arrow"
        return what + (" - " + _clean(label) if label else "")

    def mark_key(r):
        m = str(r["mark"])
        return (0, int(m), "") if m.isdigit() else (1, 0, m)

    for r in sorted([r for r in rec.get("routes", []) if r.get("mark") is not None], key=mark_key):
        label = r.get("label") or nearest(r)
        steps.append((r["mark"], describe(r, label)))
    for r in rec.get("routes", []):
        if r.get("mark") is None:
            others.append(describe(r, r.get("label") or nearest(r)))

    groups = None
    if zones:
        groups = {}
        for zt, (x0, y0, x1, y1) in zones:
            name = _clean(zt).split(". ")[0].rstrip(".")
            groups['The "%s" area' % name] = [n for n, (a0, b0, a1, b1) in cards
                                  if x0 <= a0 and y0 <= b0 and a1 <= x1 and b1 <= y1]
        loose = [n for n in (c[0] for c in cards) if not any(n in v for v in groups.values())]
        if loose:
            groups["The rest of the picture"] = loose
    return alt_text(rec.get("title", ""), parts=[c[0] for c in cards], steps=steps,
                    finding=finding if finding is not None else rec.get("subtitle"), groups=groups,
                    others=others)


def record_slides():
    """Patch slide_kit.Slide so every Slide made from now on keeps a record of what it drew, and
    Slide.save records the path instead of writing the picture. Returns the list of records."""
    sys.path.insert(0, HERE)
    import slide_kit
    S = slide_kit.Slide
    records = []
    o_init, o_zone, o_card, o_route, o_text = S.__init__, S.zone, S.card, S.route, S.text

    def __init__(self, w, h, title, subtitle=None, sizes=None):
        self._alt = {"title": title, "subtitle": subtitle, "zones": [], "cards": [], "routes": [],
                     "texts": [], "png": None}
        records.append(self._alt)
        o_init(self, w, h, title, subtitle, sizes)

    def zone(self, x, y, w, h, title, tint="plain"):
        self._alt["zones"].append((title, (x, y, x + w, y + h)))
        return o_zone(self, x, y, w, h, title, tint)

    def card(self, x, y, w, h, title, lines=(), kind="svc", mark=None):
        self._alt["cards"].append((title, (x, y, x + w, y + h)))
        return o_card(self, x, y, w, h, title, lines, kind, mark)

    def route(self, points, mark=None, label=None, *a, **kw):
        self._alt["routes"].append({"points": list(points), "mark": mark, "label": label})
        return o_route(self, points, mark, label, *a, **kw)

    def text(self, x, y, text, *a, **kw):
        self._alt["texts"].append(((x, y), text))
        return o_text(self, x, y, text, *a, **kw)

    def save(self, path):
        self._alt["png"] = os.path.abspath(path)

    S.__init__, S.zone, S.card, S.route, S.text, S.save = __init__, zone, card, route, text, save
    return records


def from_slide(slide, finding=None):
    """Alt text straight from a Slide made after record_slides(), or any object with the same record."""
    return from_record(getattr(slide, "_alt", slide), finding)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    script = os.path.abspath(argv[0])
    records = record_slides()
    sys.path.insert(0, os.path.dirname(script))
    g = {"__name__": "__main__", "__file__": script}
    old = sys.argv
    sys.argv = [script]
    try:
        with open(script, encoding="utf-8") as f:
            exec(compile(f.read(), script, "exec"), g)
    except SystemExit as e:
        if e.code not in (None, 0):
            print("the build stopped (exit status %r); alt text not written" % e.code, file=sys.stderr)
            return 1
    finally:
        sys.argv = old
    if not records:
        print("the script made no slide_kit Slide, so there is nothing to describe; call alt_text() "
              "from the script instead", file=sys.stderr)
        return 1
    for rec in records:
        alt = from_record(rec)
        print("Picture: %s\n" % (rec["png"] or "(not saved)"))
        print("Short alt (%d characters):\n%s\n" % (len(alt["short"]), alt["short"]))
        print("Long description:\n%s\n" % alt["long"])
        if "--write" in argv and rec["png"]:
            print("Wrote %s" % write_alt(rec["png"], alt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
