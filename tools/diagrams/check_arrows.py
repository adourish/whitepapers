#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check every line and arrow on a generated diagram against every box.

**Looking at the picture does not work.** On a 4,000px sheet scaled to fit a screen, an arrow that
ends 200px inside the wrong box looks like a line pointing at roughly the right place. This runs the
build with the Pillow drawing calls instrumented, records every box and every line, rebuilds the
arrows from the pieces they were drawn with, and reports three faults:

  * INSIDE   an end that lands inside a box            - the arrow points at the wrong thing
  * THROUGH  a line that passes through a box          - it reads as going through whatever it crosses
  * NOWHERE  an arrowhead that touches nothing at all  - it points into empty space

Run: python check_arrows.py path/to/build_script.py [--verbose]

What it reads (any Pillow build, nothing specific to one picture or to slide_kit):

  * boxes    - `rectangle` and `rounded_rectangle` with an outline at least 2px wide and at least
               120 x 60. A filled box drawn with no outline, then outlined with dashes, counts too:
               the dashes close into a loop, and the loop becomes the box.
               A box with no fill is a frame (a branch box, a double border): an arrow may sit inside
               it, so it is never "the wrong thing". A box that holds other boxes is a zone: arrows
               cross zones freely.
  * lines    - every `line` call 3px or wider, in every form Pillow accepts: [x0, y0, x1, y1],
               [(x0, y0), (x1, y1)], and longer polylines, which become one segment per pair of points.
               Small dots (`ellipse` 10px across or less) drawn in a row count as a dotted line.
  * arrows   - consecutive line calls in the same colour and width join into one arrow: dashes along
               the same line merge into one segment, and a piece that starts where the last one ended
               turns a corner. A small filled triangle (`polygon`) drawn right after, pointing the way the
               line runs, is the arrowhead, and its sharp point becomes the true end of the arrow. Any other drawing call ends the
               arrow being built, so two arrows that meet are never joined.

A line with no head is checked for INSIDE and THROUGH only when both its ends meet boxes (a connector,
such as a link between two tables); a lifeline, a divider, a chart's reference line or a key sample
starts in open space and is left alone. Every line counts as something an arrowhead may touch. A line drawn wholly inside one box is decoration in that
box and is not checked against it.

A build may declare `PASS_THROUGH = [(x0, y0), ...]` (top-left corners) for boxes an arrow is MEANT
to cross, such as a gate.

Exit status: 0 when clean, 1 when any fault is found, 2 when the build itself fails.
"""
import math
import os
import sys

from PIL import ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

MIN_LINE_W = 3          # thinner lines are hairlines, call-out leaders and text rules
BOX_MIN_W, BOX_MIN_H = 120, 60
JOIN_GAP = 30           # the largest gap between two pieces of one dashed or cornered line
DOT_MAX = 10            # an ellipse this small or smaller is a dot in a dotted line
HEAD_MAX = 40           # an arrowhead triangle has no side longer than this
INSIDE_DEPTH = 6        # an end more than this far inside a box is INSIDE it
THROUGH_PAD = 10        # a line must get this far into a box to pass THROUGH it
TOUCH_BOX = 14          # an arrowhead this close to a box edge touches it
TOUCH_LINE = 16         # ... or this close to another line


# ------------------------------------------------------------------ geometry helpers
def _points(xy):
    """Every form Pillow accepts for xy, as a list of (x, y)."""
    xy = list(xy)
    if not xy:
        return []
    if isinstance(xy[0], (tuple, list)):
        return [(float(p[0]), float(p[1])) for p in xy]
    return [(float(xy[i]), float(xy[i + 1])) for i in range(0, len(xy) - 1, 2)]


def _rect(xy):
    p = _points(xy)
    (x0, y0), (x1, y1) = p[0], p[1]
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _seg_dist(p, a, b):
    """Distance from point p to segment a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    if L == 0:
        return _dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return _dist(p, (a[0] + t * dx, a[1] + t * dy))


def _line_dist(p, a, b):
    """Distance from p to the infinite line through a and b."""
    L = _dist(a, b)
    if L == 0:
        return _dist(p, a)
    return abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / L


def _intersect(a, b, c, d):
    """Where the line a-b meets the line c-d, or None when they are parallel."""
    x1, y1, x2, y2 = a[0], a[1], b[0], b[1]
    x3, y3, x4, y4 = c[0], c[1], d[0], d[1]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _clip_len(a, b, r):
    """Length of segment a-b inside rectangle r (x0, y0, x1, y1), by Liang-Barsky clipping."""
    x0, y0, x1, y1 = r
    if x1 <= x0 or y1 <= y0:
        return 0.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return 0.0
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return 0.0
    return (t1 - t0) * math.hypot(dx, dy)


# ------------------------------------------------------------------ what the build drew
class Chain:
    """One line as the reader sees it: a polyline, maybe with a head at its end."""

    def __init__(self, pts, colour, width):
        self.pts = list(pts)
        self.colour, self.width = colour, width
        self.head = False
        self.sealed = False

    @property
    def start(self):
        return self.pts[0]

    @property
    def end(self):
        return self.pts[-1]

    def segments(self):
        if len(self.pts) == 1:
            return [(self.pts[0], self.pts[0])]
        return list(zip(self.pts, self.pts[1:]))

    def length(self):
        return sum(_dist(a, b) for a, b in self.segments())

    def closed(self):
        return len(self.pts) >= 4 and _dist(self.start, self.end) <= JOIN_GAP

    def try_join(self, a, b):
        """Join piece a-b onto the end of this chain if it continues it. True when joined."""
        if self.sealed:
            return False
        end = self.end
        if len(self.pts) == 1:                              # a lone dot: anything close continues it
            if _dist(end, a) <= JOIN_GAP:
                self.pts = [end, b] if a == b else [end, b]
                return True
            return False
        prev = self.pts[-2]
        if _dist(prev, end) < 1e-6:
            return False
        # straight on: the piece lies on the same line, a short gap ahead
        if _line_dist(a, prev, end) <= 2 and _line_dist(b, prev, end) <= 2:
            ux, uy = (end[0] - prev[0]), (end[1] - prev[1])
            ahead = (a[0] - end[0]) * ux + (a[1] - end[1]) * uy >= -1e-6
            if ahead and _dist(end, a) <= JOIN_GAP:
                self.pts[-1] = b if _dist(prev, b) >= _dist(prev, end) else end
                return True
            return False
        if a == b:
            return False
        # a corner: the piece starts near where this one ended and turns
        if _dist(end, a) <= JOIN_GAP:
            c = _intersect(prev, end, a, b)
            if c is not None and _dist(c, end) <= JOIN_GAP and _dist(c, a) <= JOIN_GAP:
                self.pts[-1] = c
                self.pts.append(b)
                return True
        return False


class Recorder:
    def __init__(self):
        self.boxes = []          # dict(name, r, fill, outline, kind)
        self.chains = []
        self.raw_segments = 0

    # every drawing call that is not a line ends the line being built
    def seal(self):
        if self.chains:
            self.chains[-1].sealed = True

    def add_box(self, xy, fill, outline, width):
        r = _rect(xy)
        big = (r[2] - r[0]) > BOX_MIN_W and (r[3] - r[1]) > BOX_MIN_H
        if not big:
            return
        if outline is not None and width >= 2:
            kind = "frame" if fill is None else "box"
        elif fill is not None and outline is None:
            kind = "blank"       # becomes a box only if a dashed outline closes around it
        else:
            return
        self.boxes.append({"name": "box@%d,%d" % (r[0], r[1]), "r": r, "kind": kind})

    def add_line(self, xy, fill, width):
        if width is None or width < MIN_LINE_W:
            return
        pts = _points(xy)
        for a, b in zip(pts, pts[1:]):
            self.raw_segments += 1
            self._piece(a, b, fill, width)

    def add_dot(self, xy, fill, outline):
        r = _rect(xy)
        dia = max(r[2] - r[0], r[3] - r[1])
        if fill is None or dia > DOT_MAX or dia < MIN_LINE_W:
            self.seal()
            return
        c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
        self.raw_segments += 1
        self._piece(c, c, fill, round(dia))

    def _piece(self, a, b, colour, width):
        last = self.chains[-1] if self.chains else None
        if last and last.colour == colour and last.width == width and not last.closed() \
                and last.try_join(a, b):
            return
        if last:
            last.sealed = True
        self.chains.append(Chain([a] if a == b else [a, b], colour, width))

    def add_polygon(self, xy, fill):
        pts = _points(xy)
        if len(pts) != 3 or fill is None:
            self.seal()
            return
        sides = [(_dist(pts[(i + 1) % 3], pts[(i + 2) % 3]), i) for i in range(3)]
        if max(s for s, _ in sides) > HEAD_MAX:
            self.seal()
            return
        tip = pts[min(sides)[1]]                   # the point opposite the shortest side
        base = [p for j, p in enumerate(pts) if j != min(sides)[1]]
        mid = ((base[0][0] + base[1][0]) / 2, (base[0][1] + base[1][1]) / 2)
        # the arrow it belongs to is the one just drawn, if that one ends (or starts) at the head
        point = (tip[0] - mid[0], tip[1] - mid[1])
        for ch in reversed(self.chains[-3:]):
            if ch.head:
                continue
            if min(_dist(ch.end, tip), _dist(ch.end, mid)) <= JOIN_GAP:
                last = (ch.pts[-2], ch.end) if len(ch.pts) > 1 else None
            elif min(_dist(ch.start, tip), _dist(ch.start, mid)) <= JOIN_GAP:
                last = (ch.pts[1], ch.start) if len(ch.pts) > 1 else None
            else:
                continue
            # a head points the way the line runs; a triangle pointing elsewhere is a marker
            if last is not None:
                run = (last[1][0] - last[0][0], last[1][1] - last[0][1])
                n = math.hypot(*run) * math.hypot(*point)
                if n == 0 or (run[0] * point[0] + run[1] * point[1]) / n < math.cos(math.radians(25)):
                    continue
                if last[1] == ch.start:
                    ch.pts.reverse()
            if len(ch.pts) == 1:
                ch.pts.append(tip)
            else:
                ch.pts[-1] = tip
            ch.head = True
            ch.sealed = True
            return
        self.seal()

    def name_last_box(self, xy, text):
        # the first text drawn inside a box just after it is its title, which gives it a usable name
        if not self.boxes or not self.boxes[-1]["name"].startswith("box@"):
            return
        b = self.boxes[-1]
        r = b["r"]
        if r[0] <= xy[0] <= r[2] and r[1] <= xy[1] <= r[3]:
            b["name"] = str(text).replace("\n", " ")[:34]


REC = Recorder()


def instrument():
    """Wrap Pillow's drawing calls so every box, line and arrowhead is recorded, then drawn."""
    D = ImageDraw.ImageDraw
    o_rr, o_rect, o_line, o_text = D.rounded_rectangle, D.rectangle, D.line, D.text
    o_poly, o_ell = D.polygon, D.ellipse

    depth = [0]

    def guarded(record, draw):
        """Record only the outermost call: Pillow draws some shapes by calling its other methods."""
        def wrapper(self, *a, **kw):
            if depth[0] == 0:
                record(*a, **kw)
            depth[0] += 1
            try:
                return draw(self, *a, **kw)
            finally:
                depth[0] -= 1
        return wrapper

    def r_box(xy, fill=None, outline=None, width=1):
        REC.seal()
        REC.add_box(xy, fill, outline, width)

    def r_rr(xy, radius=0, fill=None, outline=None, width=1, **kw):
        r_box(xy, fill=fill, outline=outline, width=width)

    def r_rect(xy, fill=None, outline=None, width=1, **kw):
        r_box(xy, fill=fill, outline=outline, width=width)

    def r_line(xy, fill=None, width=0, *a, **kw):
        REC.add_line(xy, fill, width)

    def r_poly(xy, fill=None, *a, **kw):
        REC.add_polygon(xy, fill)

    def r_ell(xy, fill=None, outline=None, *a, **kw):
        REC.add_dot(xy, fill, outline)

    def r_text(xy, text, *a, **kw):
        REC.seal()
        REC.name_last_box(xy, text)

    rounded_rectangle, rectangle = guarded(r_rr, o_rr), guarded(r_rect, o_rect)
    line, polygon = guarded(r_line, o_line), guarded(r_poly, o_poly)
    ellipse, text = guarded(r_ell, o_ell), guarded(r_text, o_text)

    D.rounded_rectangle, D.rectangle, D.line = rounded_rectangle, rectangle, line
    D.polygon, D.ellipse, D.text = polygon, ellipse, text


def run_build(script):
    """Run a build script as __main__ with Pillow instrumented. Returns its globals."""
    script = os.path.abspath(script)
    sys.path.insert(0, os.path.dirname(script))
    sys.path.insert(0, HERE)
    g = {"__name__": "__main__", "__file__": script}
    argv = sys.argv
    sys.argv = [script]
    try:
        with open(script, encoding="utf-8") as f:
            code = compile(f.read(), script, "exec")
        exec(code, g)
    except SystemExit as e:
        if e.code not in (None, 0):
            raise RuntimeError("the build stopped with exit status %r before saving" % e.code)
    finally:
        sys.argv = argv
    return g


# ------------------------------------------------------------------ turning records into a picture
def resolve():
    """Close dashed loops into boxes, drop box outlines, sort boxes into leaves, frames and zones."""
    boxes = [b for b in REC.boxes]
    chains = []
    for ch in REC.chains:
        if ch.closed() and not ch.head:
            xs = [p[0] for p in ch.pts]
            ys = [p[1] for p in ch.pts]
            r = (min(xs), min(ys), max(xs), max(ys))
            if (r[2] - r[0]) > BOX_MIN_W and (r[3] - r[1]) > BOX_MIN_H:
                match = [b for b in boxes if b["kind"] == "blank"
                         and all(abs(b["r"][i] - r[i]) <= 4 for i in range(4))]
                if match:
                    match[0]["kind"] = "box"
                else:
                    boxes.append({"name": "dashed box@%d,%d" % (r[0], r[1]), "r": r, "kind": "box"})
            continue                                   # a closed outline is a box, never an arrow
        chains.append(ch)
    boxes = [b for b in boxes if b["kind"] != "blank"]

    # an outline drawn as separate straight lines along a box edge is part of the box, not an arrow
    def on_edge(ch):
        if ch.head or len(ch.pts) != 2:
            return False
        (ax, ay), (bx, by) = ch.pts
        for b in boxes:
            x0, y0, x1, y1 = b["r"]
            for ex0, ey0, ex1, ey1 in ((x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)):
                if _seg_dist((ax, ay), (ex0, ey0), (ex1, ey1)) <= 3 and \
                        _seg_dist((bx, by), (ex0, ey0), (ex1, ey1)) <= 3:
                    return True
        return False
    chains = [c for c in chains if not on_edge(c)]

    for b in boxes:
        b["zone"] = False
    for b in boxes:
        if b["kind"] != "box":
            continue
        x0, y0, x1, y1 = b["r"]
        area = (x1 - x0) * (y1 - y0)
        for o in boxes:
            if o is b:
                continue
            p0, q0, p1, q1 = o["r"]
            # a filled box inside it, or anything much smaller: a zone. A frame drawn just inside
            # it (a double border) does not make it a zone.
            if x0 <= p0 and y0 <= q0 and p1 <= x1 and q1 <= y1 and                     (o["kind"] == "box" or area > 1.6 * (p1 - p0) * (q1 - q0)):
                b["zone"] = True
                break
    return boxes, chains


def inside(p, r, depth=INSIDE_DEPTH):
    return r[0] + depth < p[0] < r[2] - depth and r[1] + depth < p[1] < r[3] - depth


def edge_dist(p, r):
    """How far p is from the outline of r (0 on the outline)."""
    x0, y0, x1, y1 = r
    if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
        return min(p[0] - x0, x1 - p[0], p[1] - y0, y1 - p[1])
    dx = max(x0 - p[0], 0, p[0] - x1)
    dy = max(y0 - p[1], 0, p[1] - y1)
    return math.hypot(dx, dy)


def check(boxes, chains, pass_through=()):
    def is_pass(b):
        return any(abs(b["r"][0] - r[0]) < 4 and abs(b["r"][1] - r[1]) < 4 for r in pass_through)

    targets = [b for b in boxes if b["kind"] == "box" and not b["zone"] and not is_pass(b)]
    faults = []

    def label(i, ch):
        return "%s %d (%d,%d)->(%d,%d)" % ("arrow" if ch.head else "line", i, ch.start[0], ch.start[1],
                                          ch.end[0], ch.end[1])

    def touches(p):
        return any(edge_dist(p, b["r"]) <= TOUCH_BOX or inside(p, b["r"], 0) for b in targets)

    for i, ch in enumerate(chains):
        # a line with no head is only judged as a connector, when both its ends meet boxes: a
        # lifeline, a divider, a chart's reference line or a key sample starts in open space
        if not ch.head and not (touches(ch.start) and touches(ch.end)):
            continue
        # a box that holds both ends holds the whole line: the line is drawn in it, not at it
        own = [b for b in targets if not (inside(ch.start, b["r"], 0) and inside(ch.end, b["r"], 0))]
        ends = (("start", ch.start), ("end", ch.end)) if len(ch.pts) > 1 else (("dot", ch.start),)
        end_boxes = set()
        for which, p in ends:
            hits = [b for b in own if inside(p, b["r"])]
            for b in hits:
                end_boxes.add(id(b))
            if hits:
                faults.append("INSIDE   %s: %s (%d,%d) is inside  %s"
                              % (label(i, ch), which, p[0], p[1], ", ".join(b["name"] for b in hits)))
        for b in own:
            if id(b) in end_boxes:
                continue
            x0, y0, x1, y1 = b["r"]
            core = (x0 + THROUGH_PAD, y0 + THROUGH_PAD, x1 - THROUGH_PAD, y1 - THROUGH_PAD)
            if any(_clip_len(a, c, core) > 1 for a, c in ch.segments()):
                faults.append("THROUGH  %s passes through  %s" % (label(i, ch), b["name"]))
        if ch.head and not any(inside(ch.end, b["r"]) for b in own):     # INSIDE already said it
            tip = ch.end
            near_box = any(edge_dist(tip, b["r"]) <= TOUCH_BOX for b in boxes)
            near_line = any(_seg_dist(tip, a, c) <= TOUCH_LINE
                            for j, o in enumerate(chains) if j != i for a, c in o.segments())
            if not (near_box or near_line):
                faults.append("NOWHERE  %s: its head (%d,%d) touches nothing" % (label(i, ch), tip[0], tip[1]))
    return faults


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    instrument()
    try:
        g = run_build(argv[0])
    except Exception as e:                                         # noqa: BLE001
        print("the build failed, so nothing was checked: %s" % e, file=sys.stderr)
        return 2
    boxes, chains = resolve()
    faults = check(boxes, chains, list(g.get("PASS_THROUGH", [])))
    n_box = sum(1 for b in boxes if b["kind"] == "box")
    print("boxes: %d (%d zones, %d frames)   segments: %d   lines: %d   arrows: %d\n"
          % (n_box, sum(1 for b in boxes if b["zone"]), sum(1 for b in boxes if b["kind"] == "frame"),
             REC.raw_segments, len(chains), sum(1 for c in chains if c.head)))
    if "--verbose" in argv or "-v" in argv:
        for b in boxes:
            print("  %-5s %-34s (%d,%d)-(%d,%d)" % ("zone" if b["zone"] else b["kind"], b["name"], *b["r"]))
        for i, c in enumerate(chains):
            print("  %-5s %d  %s  width %s %s" % ("arrow" if c.head else "line", i,
                  " -> ".join("(%d,%d)" % p for p in c.pts), c.width, c.colour))
        print()
    for f in faults:
        print(f)
    print("\n%d fault%s" % (len(faults), "" if len(faults) == 1 else "s"))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
