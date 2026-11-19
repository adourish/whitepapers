#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""How the timeout lab is set up and how each test was run, as two page-width pictures.

    python build_lab_setup.py   ->  lab-setup-apps.png, lab-setup-run.png and an .alt.md for each

lab-setup-apps.png: the apps and the two numbered calls of one Print; the switches run_lab.py sets
for each run; the trouble it causes on purpose; what is measured.
lab-setup-run.png: the steps of one run, lettered A to H, then how results are repeated and written.
Both are sized for 7 inches wide on a Word page: at most 9 inches tall, body text 8 point or more.
Both are saved, or neither.

Every number on the picture is read from the lab's own files, not typed in:
  * ports, the database pool, the round trips and their delay from the two application.properties;
  * the worker pool (core, max, queue) from the @Value defaults in WorkDataApp.java;
  * the give-up time, the health check's pause and the counter sampling from LoadTest.java;
  * the two numbered calls from the order of the calls in NoticeApp.generatePrintNotices();
  * the error codes from NoticeApp.java's answers;
  * every switch value, fault, load size, repeat count and the warm-up from the runs listed in
    run_lab.py (the module is loaded; its main() is not run), and the order of a run's steps
    from run_lab.one().
The build refuses to save when any of these can no longer be found, when the steps drawn no longer
match the code's order, when a box has no arrow and is not a note, when the lettered steps skip a
letter, when the key misses or over-explains something drawn, when a card runs past its panel,
when two card fills look alike to a colour-blind reader, or when a picture is too tall or its
text too small for the page.
"""
import importlib.util
import inspect
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", "lab"))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools", "diagrams"))
sys.path.insert(0, TOOLS)
from slide_kit import Slide                                  # noqa: E402
from diagram_style import INK, SVC_F, TOUCH_F, STORE_F, BOTTLE_F, STORY_E   # noqa: E402
from write_alt_text import alt_text, write_alt              # noqa: E402

SCRIPT = "papers/printing-hang-fixes-compared/assets/build_lab_setup.py"

NOTICE_PROPS = ("notice-app", "src", "main", "resources", "application.properties")
WORK_PROPS = ("work-data-app", "src", "main", "resources", "application.properties")
NOTICE_JAVA = ("notice-app", "src", "main", "java", "lab", "notice", "NoticeApp.java")
WORK_JAVA = ("work-data-app", "src", "main", "java", "lab", "workdata", "WorkDataApp.java")
LOAD_JAVA = ("loadtest", "LoadTest.java")
RUN_LAB = ("run_lab.py",)


def refuse(why):
    print("NOT WRITTEN - " + why, file=sys.stderr)
    sys.exit(1)


def _read(parts):
    path = os.path.join(LAB, *parts)
    if not os.path.exists(path):
        refuse(f"{'/'.join(parts)} is missing")
    with open(path, encoding="utf-8") as f:
        return f.read()


def _prop(parts, key):
    m = re.search(r"^\s*" + re.escape(key) + r"\s*=\s*(.+?)\s*$", _read(parts), re.M)
    if not m:
        refuse(f"{'/'.join(parts)} no longer sets {key}")
    return m.group(1)


def _int_prop(parts, key):
    v = _prop(parts, key)
    if not v.isdigit():
        refuse(f"{'/'.join(parts)}: {key} is not a whole number ({v!r})")
    return int(v)


def _value_default(parts, key):
    m = re.search(r'@Value\("\$\{' + re.escape(key) + r':(\d+)\}"\)', _read(parts))
    if not m:
        refuse(f"{'/'.join(parts)} no longer has a number default for {key}")
    return int(m.group(1))


def _search(parts, pattern, why, flags=0):
    m = re.search(pattern, _read(parts), flags)
    if not m:
        refuse(why)
    return m


def _seconds(n):
    """20 -> '20 seconds', 300 -> '5 minutes'."""
    return f"{n // 60} minutes" if n % 60 == 0 and n >= 120 else f"{n} seconds"


def _or(items):
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " or " + items[-1]


# ------------------------------------------------------------------ the apps (properties and code)
NOTICE_PORT = _int_prop(NOTICE_PROPS, "server.port")
WORK_PORT = _int_prop(WORK_PROPS, "server.port")
_m = re.search(r"jdbc:h2:tcp://[^:/]+:(\d+)/", _prop(WORK_PROPS, "spring.datasource.url"))
if not _m:
    refuse("work-data-app no longer points at an H2 database server over the network (jdbc:h2:tcp)")
DB_PORT = int(_m.group(1))
DB_POOL = _int_prop(WORK_PROPS, "spring.datasource.hikari.maximum-pool-size")
LATENCY_MS = _int_prop(WORK_PROPS, "lab.db.latency-ms")
ROUND_TRIPS = _int_prop(WORK_PROPS, "lab.db.round-trips-per-notice")
CORE = _value_default(WORK_JAVA, "lab.executor.core")
MAX = _value_default(WORK_JAVA, "lab.executor.max")
QUEUE = _value_default(WORK_JAVA, "lab.executor.queue")

GIVE_UP_S = int(_search(LOAD_JAVA, r'getOrDefault\("timeout",\s*"(\d+)"\)',
                        "loadtest/LoadTest.java no longer has a default give-up time (--timeout)").group(1))
PROBE_MS = int(_search(LOAD_JAVA, r"Thread prober.*?sleep\((\d+)\)",
                       "loadtest/LoadTest.java no longer pauses between health checks", re.S).group(1))
SAMPLE_MS = int(_search(LOAD_JAVA, r"Thread sampler.*?sleep\((\d+)\)",
                        "loadtest/LoadTest.java no longer pauses between reading the apps' counters",
                        re.S).group(1))
PROBE_TEXT = {500: "twice a second", 1000: "once a second"}.get(PROBE_MS, f"every {PROBE_MS} ms")
SAMPLE_TEXT = (f"every {SAMPLE_MS // 1000} seconds" if SAMPLE_MS % 1000 == 0
               else f"every {SAMPLE_MS} milliseconds")

_notice = _read(NOTICE_JAVA)
for _key in ("lab.client.connect-timeout-ms", "lab.client.read-timeout-ms"):
    _int_prop(NOTICE_PROPS, _key)
for _sw in ("lab.client.breaker", "lab.client.bulkhead"):
    if _sw not in _notice:
        refuse(f"NoticeApp.java no longer has the {_sw} switch")


def _code_after(exception):
    m = re.search(r"catch \(" + exception + r" e\).*?status\((\d+)\)", _notice, re.S)
    if not m:
        refuse(f"NoticeApp.java no longer answers {exception} with an HTTP status")
    return int(m.group(1))


GAVE_UP_CODE = _code_after("ResourceAccessException")
BULKHEAD_CODE = _code_after("BulkheadFullException")
BREAKER_CODE = _code_after("CallNotPermittedException")
REFUSED_CODES = sorted({BULKHEAD_CODE, BREAKER_CODE})

# ------------------------------------------------------------------ the runs (run_lab.py)
_spec = importlib.util.spec_from_file_location("run_lab", os.path.join(LAB, *RUN_LAB))
run_lab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_lab)                 # defines RUNS; main() is not called
RUNS = run_lab.RUNS
if not RUNS:
    refuse("run_lab.py lists no runs")
_defaults = {k: p.default for k, p in inspect.signature(run_lab.run).parameters.items()
             if p.default is not inspect.Parameter.empty}
NORMAL_USERS = _defaults["users"]
POOL_KEY = "spring.datasource.hikari.maximum-pool-size"

JAVAS = sorted({c["jdk"] for c in RUNS} | {c["wd_jdk"] for c in RUNS})
VIRTUAL = {c["virtual"] for c in RUNS}
LIMITS = sorted({(c["ns"].get("lab.client.connect-timeout-ms", 0), c["ns"].get("lab.client.read-timeout-ms", 0))
                 for c in RUNS})
BREAKER_MODES = {c["ns"].get("lab.client.breaker.record", "all") for c in RUNS
                 if c["ns"].get("lab.client.breaker") == "true"}
BULKHEADS = sorted({int(c["ns"].get("lab.client.bulkhead", 0)) for c in RUNS})
POOLS = sorted({int(c["wd"].get(POOL_KEY, DB_POOL)) for c in RUNS})
HOLD_LOCK = any(c["wd"].get("lab.db.hold-lock") == "true" for c in RUNS)
CPU_WORK = any("lab.cpu.kb-per-notice" in c["wd"] for c in RUNS)
STALLS = sorted({c["seconds"] for c in RUNS if c["stall"] == "hang"})
SLOWS = sorted({int(c["stall"][5:]) // 1000 for c in RUNS if c["stall"] and c["stall"].startswith("slow:")})
DOWN = any(c["down"] for c in RUNS)
UNREACHABLE = any(c["blackhole"] for c in RUNS)
OVERLOAD_USERS = sorted({c["users"] for c in RUNS if c["users"] > NORMAL_USERS and not c["stall"]
                         and not c["down"] and not c["blackhole"] and not c["wd"]})
USERS = sorted({c["users"] for c in RUNS})
SECONDS = sorted({c["seconds"] for c in RUNS})
REPEATS = sorted({c["repeats"] for c in RUNS})
REPEATED = sum(1 for c in RUNS if c["repeats"] > 1)

if len(JAVAS) != 2 or VIRTUAL != {False, True}:
    refuse(f"run_lab.py no longer compares two Java versions with and without virtual threads: {JAVAS}, {VIRTUAL}")
for name, val in (("time limits", len(LIMITS) > 1), ("circuit breaker", BREAKER_MODES),
                  ("bulkhead", len(BULKHEADS) > 1), ("database pool", len(POOLS) > 1),
                  ("driver lock", HOLD_LOCK), ("processor work", CPU_WORK), ("stall", STALLS),
                  ("slow answers", SLOWS), ("not running", DOWN), ("unreachable address", UNREACHABLE),
                  ("overload", OVERLOAD_USERS)):
    if not val:
        refuse(f"run_lab.py no longer has any run with the {name} switch or fault")
if REPEATS[-1] < 3 or REPEATED == 0:
    refuse("run_lab.py no longer repeats any run 3 times or more")
if "def mid(" not in _read(RUN_LAB) or "len(s) // 2" not in _read(RUN_LAB):
    refuse("run_lab.py no longer reports the middle of the repeats")
for out in ("results.json", "RESULTS.md"):
    if f'"{out}"' not in _read(RUN_LAB):
        refuse(f"run_lab.py no longer writes {out}")
_m = re.search(r"load\(c, (\d+), (\d+), .*?warmup", _read(RUN_LAB))
if not _m:
    refuse("run_lab.py no longer warms the apps up before measuring")
WARM_USERS, WARM_S = int(_m.group(1)), int(_m.group(2))


def _limit_text(conn, read):
    return "none" if conn == 0 and read == 0 else f"{conn // 1000} + {read // 1000}"


LIMIT_TEXT = _or([_limit_text(*lim) for lim in LIMITS])
BREAKER_TEXT = " or ".join(
    {"all": "counting every error", "timeouts": "counting only time-outs"}[m] for m in sorted(BREAKER_MODES))
BULKHEAD_TEXT = _or(["off" if b == 0 else str(b) for b in BULKHEADS])

# ------------------------------------------------------------------ the data
# One Print: (number, label on the arrow, the work-data endpoint it calls)
CALLS = [(1, "make the tickets", "createNotices"),
         (2, "mark them printed", "updateNotices")]
LABEL = {n: lab for n, lab, _ in CALLS}

# One run: (letter, heading, body lines, the text in run_lab.one() that does it)
RUN_STEPS = [
    ("A", "Start the database", ["H2 server, its own", f"program, port {DB_PORT}"], "org.h2.tools.Server"),
    ("B", "Start work-data", ["Left out for the", "'not running' fault"], "WD_JAR"),
    ("C", "Start notice-app", ["With this run's", "switches"], "NS_JAR"),
    ("D", "Warm up", [f"{WARM_USERS} people for {WARM_S}", "seconds, not counted"], "warmup"),
    ("E", "Switch on the fault", ["Stops answering or", "slow, if this run has it"], "admin/stall"),
    ("F", "Run the load", [f"{USERS[0]} to {USERS[-1]} people, for", f"{_seconds(SECONDS[0])} to {_seconds(SECONDS[-1])}"],
     'load(c, c["users"]'),
    ("G", "Collect the counts", ["From the load generator", "and both apps"], "return json.load"),
    ("H", "Stop everything", ["A fresh start for", "the next run"], "p.kill()"),
]


def check_run_order(s):
    """The lettered steps follow the order of the code in run_lab.one() (and load())."""
    src = inspect.getsource(run_lab.one)
    src_load = inspect.getsource(run_lab.load)
    pos = []
    for letter, _, _, marker in RUN_STEPS:
        if marker == "return json.load":     # G happens inside load(), called at step F
            i = src.find('load(c, c["users"]')
            if marker not in src_load:
                s.problems.append("step G: load() in run_lab.py no longer collects the counts")
            pos.append(i + 1 if i >= 0 else -1)
        else:
            pos.append(src.find(marker))
    missing = [RUN_STEPS[i][0] for i, p in enumerate(pos) if p < 0]
    if missing:
        s.problems.append(f"run steps {missing} are no longer found in run_lab.one()")
    elif pos != sorted(pos):
        s.problems.append(f"run steps A to H do not follow the order of run_lab.one(): {pos}")


def calls_in_generate():
    m = re.search(r"generatePrintNotices\(.*?\n    \}", _notice, re.S)
    if not m:
        refuse("NoticeApp.java no longer has a generatePrintNotices() method")
    return re.findall(r"/api/print-notices/(\w+)", m.group(0))


# ------------------------------------------------------------------ the drawing
# Both pictures are shown 7 inches wide on a Word page. At W = 2000 px, 8 point text needs
# 8 / 72 * 2000 / 7 = 31.7 px, so body text is 32 px; a page holds at most 9 inches, so H <= 2571.
W = 2000
PAGE_IN, MIN_PT, MAX_TALL_IN = 7.0, 8.0, 9.0
SIZES = {"title": 52, "sub": 32, "zone": 36, "head": 34, "body": 32, "edge": 32}
TROUBLE_F, TROUBLE_INK = STORY_E, "#FFFFFF"     # trouble cards: dark magenta, white words


def _rel_lum(hexc):
    c = [int(hexc.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a, b):
    la, lb = sorted((_rel_lum(a), _rel_lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_fills(pic, fills):
    """Every pair of card fills on the picture stays tellable apart for colour-blind readers
    (delta E 6 or more, as check_colour_blind.py asks; the square database card is told apart by
    its corners, as that check allows), and the trouble fill also in greyscale;
    words on the trouble cards keep a 4.5 to 1 contrast."""
    import check_colour_blind as cb
    names = list(fills)
    for i, na in enumerate(names):
        for nb in names[i + 1:]:
            trouble = TROUBLE_F in (fills[na], fills[nb])
            if "square" in (na, nb) and not trouble:
                continue                     # square corners already tell the database apart
            views = ["protanopia", "deuteranopia", "tritanopia"] + (["greyscale"] if trouble else [])
            for v in views:
                d = cb.delta_e2000(cb.simulate(cb.hex_rgb(fills[na]), v),
                                   cb.simulate(cb.hex_rgb(fills[nb]), v))
                if d < 6:
                    pic.s.problems.append(f"card fills {na} and {nb} look alike in {v} (delta E {d:.1f})")
    if _contrast(TROUBLE_F, TROUBLE_INK) < 4.5:
        pic.s.problems.append("words on the trouble cards are below 4.5 to 1 contrast")


class Pic:
    """One picture: the slide plus what is drawn on it, so the checks can see it."""

    def __init__(self, h, title, subtitle):
        self.s = Slide(W, h, title, subtitle, sizes=SIZES)
        self.cards, self.arrows, self.trouble = [], [], False
        tall = PAGE_IN * h / W
        if tall > MAX_TALL_IN:
            self.s.problems.append(f"{title!r} is {tall:.1f} inches tall at {PAGE_IN:.0f} inches wide; "
                                   f"a page holds {MAX_TALL_IN:.0f}")
        if SIZES["body"] / W * PAGE_IN * 72 < MIN_PT - 0.5:
            self.s.problems.append(f"body text prints below {MIN_PT:.0f} point at {PAGE_IN:.0f} inches wide")

    def card(self, x, y, w, hh, title, lines=(), kind="svc", note=False, mark=None):
        if kind == "trouble":
            box = self._trouble_card(x, y, w, hh, title, lines)
            self.trouble = True
        else:
            box = self.s.card(x, y, w, hh, title, lines, kind=kind, mark=mark)
        self.cards.append((title, box, kind, note, mark))
        return box

    def _trouble_card(self, x, y, w, hh, title, lines):
        s = self.s
        s.d.rounded_rectangle([x, y, x + w, y + hh], 10, fill=TROUBLE_F, outline=TROUBLE_F, width=3)
        s._check_width(title, s.F_HEAD, w - 32, title)
        s.d.text((x + 16, y + 16), title, fill=TROUBLE_INK, font=s.F_HEAD)
        ty = y + 16 + s.F_HEAD.size + 10
        for ln in lines:
            s._check_width(ln, s.F_BODY, w - 32, title)
            s.d.text((x + 16, ty), ln, fill=TROUBLE_INK, font=s.F_BODY)
            ty += s.F_BODY.size + 8
        if ty - 8 + 16 > y + hh:
            s.problems.append(f"text runs past the bottom of {title!r}")
        s.boxes.append((title, (x, y, x + w, y + hh)))
        s._on_canvas(title, x, y, x + w, y + hh)
        return (x, y, x + w, y + hh)

    def route(self, points, mark=None, text=None, side="right"):
        self.s.route(points, mark, text, side=side)
        self.arrows.append((points, mark, False))

    def label(self, x, y, lines, anchor="mm"):
        for i, ln in enumerate(lines):
            self.s.text(x, y + i * 40, ln, bold=True, anchor=anchor)

    def section(self, y, title):
        self.s._check_width(title, self.s.F_ZONE, W - 80, "section heading")
        self.s.d.text((40, y), title, fill=INK, font=self.s.F_ZONE)

    def check(self, key_items):
        s = self.s
        for title, box, kind, note, _ in self.cards:
            if not note and not any(_touches(p[0], box) or _touches(p[-1], box) for p, _, _ in self.arrows):
                s.problems.append(f"no arrow reaches {title!r}: draw its arrow, or mark it as a note")
        letters = [m for *_, m in self.cards if m]
        if letters != [chr(ord("A") + i) for i in range(len(letters))]:
            s.problems.append(f"the lettered run steps do not run A, B, C ... without gaps: {letters}")
        used = {k for _, _, k, _, _ in self.cards if k != "svc"}
        used |= {"solid" for _ in self.arrows[:1]}
        used |= {"step" for _, m, _ in self.arrows if m and str(m).isdigit()}
        used |= {"setup" for *_, m in self.cards if m}
        keyed = {k for k, _, _ in key_items}
        for k in sorted(used - keyed):
            s.problems.append(f"the key has no sample for {k!r}, which is on the picture")
        for k in sorted(keyed - used):
            s.problems.append(f"the key explains {k!r}, which is not on the picture")

    def keys(self, items, per_row):
        """The key in rows of per_row, the last row along the footer. A trouble sample is drawn in
        the trouble colours over the slide kit's own sample."""
        s = self.s
        rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
        base = s.H - 20 - s.foot_h - 70
        for r, row in enumerate(rows):
            y = base - (len(rows) - 1 - r) * 110
            s.key([("rule" if k == "trouble" else k, m, t) for k, m, t in row], y=y)
            col = (W - 120) // len(row)
            for i, (k, _, _) in enumerate(row):
                if k == "trouble":
                    x, cy = 60 + i * col, y + 5
                    s.d.rectangle([x - 2, cy - 20, x + 42, cy + 20], fill="#FAFBFC")
                    s.d.rounded_rectangle([x, cy - 18, x + 40, cy + 18], 6, fill=TROUBLE_F, outline=TROUBLE_F, width=3)


def _touches(p, box, slack=3):
    x, y = p
    return box[0] - slack <= x <= box[2] + slack and box[1] - slack <= y <= box[3] + slack


def h(n):
    """Card height for n body lines at these font sizes."""
    return 16 + SIZES["head"] + 10 + n * (SIZES["body"] + 8) + 16


# ================================================================== picture 1: the setup
def build_apps():
    H1 = 2560
    p1 = Pic(H1, "How the lab is set up",
             f"Follow 1 and 2 for one Print.  {len(RUNS)} runs, each with its own switches and trouble.")
    s = p1.s
    if [c for _, _, c in CALLS] != calls_in_generate():
        s.problems.append(f"calls {[c for _, _, c in CALLS]} do not match generatePrintNotices(): {calls_in_generate()}")

    p1.section(150, "1.  The apps, and one Print")
    R1 = 210
    s.zone(30, R1, 640, 70 + h(3) + 20 + h(2) + 30, "Callers")
    people = p1.card(60, R1 + 70, 580, h(3), "People pressing Print",
                     ["A load generator; each", f"gives up after {GIVE_UP_S} seconds", "and presses again"])
    health = p1.card(60, people[3] + 20, 580, h(2), "Health check", [f"Asks notice-app {PROBE_TEXT}",
                                                                     "\"are you up?\"; calls nothing"])
    ROW1_H = health[3] + 30 - R1
    s.zone(930, R1, 1040, ROW1_H, "Ticket service stand-in - people wait on it", tint="new")
    notice = p1.card(960, R1 + 70, 980, max(h(4), health[3] - (R1 + 70)), "notice-app", [
        f"Stands in for the ticket service, port {NOTICE_PORT}",
        "Answers Print only after both calls",
        "to work-data have answered",
        "Its web client's guards: see 2"], kind="new")

    R2 = R1 + ROW1_H + 100
    db_lines = [f"The shop's database, port {DB_PORT}",
                f"Waits {LATENCY_MS} milliseconds per",
                "answer, like the trip over the",
                "wide area network (WAN)",
                "to the real one (40 to 80)"]
    ROW2_H = 70 + h(len(db_lines)) + 30
    s.zone(930, R2, 1040, ROW2_H, "Order-data stand-in", tint="new")
    work = p1.card(960, R2 + 70, 980, h(4), "work-data-app", [
        f"Stands in for the order-data service, port {WORK_PORT}",
        f"Worker pool: {CORE} to {MAX} threads, plus {QUEUE} queued;",
        "when all are full it refuses the work",
        f"Database connection pool: {DB_POOL}"], kind="new")
    s.zone(30, R2, 640, ROW2_H, "Database stand-in", tint="outside")
    db = p1.card(60, R2 + 70, 580, h(len(db_lines)), "H2 database server", db_lines, kind="store")

    Y_P, Y_H = people[1] + 60, health[1] + 60
    p1.route([(people[2], Y_P), (notice[0], Y_P)])
    p1.label((people[2] + notice[0]) / 2, Y_P - 36, ["Print"])
    p1.route([(health[2], Y_H), (notice[0], Y_H)])
    p1.label((health[2] + notice[0]) / 2, Y_H - 36, ["are you up?"])
    X1, X2 = 1380, 1580
    p1.route([(X1, notice[3]), (X1, work[1])], "1", LABEL[1], side="left")
    p1.route([(X2, notice[3]), (X2, work[1])], "2", LABEL[2], side="right")
    Y_DB = work[1] + 60
    p1.route([(work[0], Y_DB), (db[2], Y_DB)])
    p1.label((work[0] + db[2]) / 2, Y_DB - 78, [f"{ROUND_TRIPS} round trips", "per ticket"])
    p1.label((work[0] + db[2]) / 2, Y_DB + 38, ["each", f"{LATENCY_MS} milliseconds"])

    # ---- 2, 3, 4 side by side
    PY = R2 + ROW2_H + 50
    COLS = [(30, 640), (685, 630), (1335, 635)]
    PANEL_H = 1060
    for (x, w), title in zip(COLS, ["2.  Switches for each run", "3.  Trouble on purpose", "4.  What is measured"]):
        s.zone(x, PY, w, PANEL_H, title)

    x, w = COLS[0][0] + 20, COLS[0][1] - 40
    sw1 = p1.card(x, PY + 70, w, h(13), "Set on notice-app", [
        f"Java {_or(JAVAS)}",
        "Virtual threads: on or off",
        "Time limits on its web client,",
        "seconds to connect + to wait:",
        f"{LIMIT_TEXT}",
        "Circuit breaker (stops calling",
        "a while after failures): off,",
        f"or on, {BREAKER_TEXT.split(' or ')[0]}",
        f"or {BREAKER_TEXT.split(' or ')[1]}" if " or " in BREAKER_TEXT else "",
        "Bulkhead (cap on calls to",
        f"work-data at once): {BULKHEAD_TEXT}",
        "Some runs put work-data on",
        "a different Java"], kind="wait", note=True)
    p1.card(x, sw1[3] + 20, w, h(6), "Set on work-data-app", [
        f"Database pool: {_or(POOLS)}",
        "A database driver that holds",
        "a lock while it waits: on/off",
        "PDF-like processor work",
        "(PDF: Portable Document",
        "Format files): on or off"], kind="wait", note=True)

    x, w = COLS[1][0] + 20, COLS[1][1] - 40
    s.text(x, PY + 86, "All put into work-data-app:", anchor="lm")
    FAULTS = [
        ("Stops answering", ["Takes calls, never answers,", f"for {' or '.join(_seconds(n) for n in STALLS)}"]),
        ("Slow", [f"Answers after {' or '.join(_seconds(n) for n in SLOWS)}"]),
        ("Not running", ["work-data never started"]),
        ("Address does not answer", ["notice-app calls an address", "where nothing listens"]),
        ("Overload", [f"{_or(OVERLOAD_USERS)} people, not {NORMAL_USERS}"]),
    ]
    fy = PY + 116
    for head, lines in FAULTS:
        b = p1.card(x, fy, w, h(len(lines)), head, lines, kind="trouble", note=True)
        fy = b[3] + 20
    p1.card(x, fy, w, h(2), "No trouble", [f"Normal load: {NORMAL_USERS} people,", "to compare against"], note=True)

    x, w = COLS[2][0] + 20, COLS[2][1] - 40
    m1 = p1.card(x, PY + 70, w, h(10), "Seen by the people", [
        "Prints answered OK, a second",
        "How long they waited: the",
        "middle, and the slowest 1 in 20",
        "Named errors: time limit ran",
        f"out (HTTP {GAVE_UP_CODE}); breaker or",
        f"bulkhead said no (HTTP {_or(REFUSED_CODES)})",
        "Health checks answered, out",
        f"of those sent ({PROBE_TEXT})",
        "HTTP: the web's request rules;",
        "the number is its answer code"], note=True)
    p1.card(x, m1[3] + 20, w, h(6), "Read from both apps", [
        f"Their counters, {SAMPLE_TEXT}:",
        "stuck calls (still waiting in",
        "notice-app), threads, memory,",
        "database connections in use,",
        "refusals by the worker pool,",
        "breaker and bulkhead"], note=True)

    for title, box, *_ in p1.cards:
        if PY <= box[1] < PY + PANEL_H and box[3] > PY + PANEL_H - 15:
            s.problems.append(f"{title!r} runs past the bottom of its panel")
    check_fills(p1, {"white": SVC_F, "cyan": TOUCH_F, "square": STORE_F, "yellow": BOTTLE_F, "trouble": TROUBLE_F})

    KEY1 = [("step", "1", "A call in one Print"), ("solid", None, "Arrow: a call that waits"),
            ("new", None, "Cyan: an app for the lab"), ("store", None, "Square: the database"),
            ("wait", None, "Yellow: a switch"), ("trouble", None, "Dark magenta: trouble")]
    p1.check(KEY1)
    s.footer(f"Generated by {SCRIPT} from run_lab.py, both apps' application.properties and Java code, "
             f"and LoadTest.java - do not hand-edit.")
    p1.keys(KEY1, 3)
    if (p1.s.key_box[1] - 110) < PY + PANEL_H + 20:
        s.problems.append("the key reaches up into the panels")
    return p1


# ================================================================== picture 2: one run
def build_run():
    CW, GAP = 425, 60
    ROWS_Y = [230, 230 + h(2) + 100]
    REPEAT_Y = ROWS_Y[1] + h(2) + 40
    ZONE_H = REPEAT_Y + h(3) + 30 - 150
    H2 = 150 + ZONE_H + 40 + 100 + 60
    p2 = Pic(H2, "How each lab test was run",
             f"run_lab.py does steps A to H for every one of its {len(RUNS)} runs, in this order.")
    s2 = p2.s
    check_run_order(s2)
    s2.zone(30, 150, 1940, ZONE_H, "One run, from a fresh start to a clean stop")
    xs = [60 + i * (CW + GAP) for i in range(4)]
    boxes = [p2.card(xs[i % 4], ROWS_Y[i // 4], CW, h(2), head, lines, mark=letter)
             for i, (letter, head, lines, _) in enumerate(RUN_STEPS)]
    for a, b in zip(boxes, boxes[1:]):
        if a[1] == b[1]:
            yy = (a[1] + a[3]) // 2
            p2.route([(a[2], yy), (b[0], yy)])
        else:
            mx, gy, bx = (a[0] + a[2]) // 2, (a[3] + b[1]) // 2, (b[0] + b[2]) // 2
            p2.route([(mx, a[3]), (mx, gy), (bx, gy), (bx, b[1])])
    p2.card(60, REPEAT_Y, 1880, h(3), "Then: repeat, keep the middle, write it down", [
        f"{REPEATED} of the {len(RUNS)} runs (the core scenarios) are run {REPEATS[-1]} times; the middle",
        "result is reported, with the range across the repeats",
        "Results are written to results/results.json and results/RESULTS.md"], note=True)
    KEY2 = [("setup", "A", "A step in one run, in order"), ("solid", None, "Arrow: then the next step")]
    p2.check(KEY2)
    s2.footer(f"Generated by {SCRIPT} from run_lab.py and LoadTest.java - do not hand-edit.")
    p2.keys(KEY2, 2)
    return p2


# LAB_DIAGRAM_ONLY=apps or =run builds just one picture and saves nothing, so a checker that
# records what is drawn (check_arrows.py) sees one picture at a time.
ONLY = os.environ.get("LAB_DIAGRAM_ONLY")
if ONLY:
    pic = build_apps() if ONLY == "apps" else build_run()
    if pic.s.problems:
        refuse("the picture has defects: " + "; ".join(pic.s.problems))
    print("Checked", ONLY, "- nothing saved")
    sys.exit(0)
p1 = build_apps()
p2 = build_run()

# ================================================================== save both, or neither
OUT1 = os.path.join(HERE, "lab-setup-apps.png")
OUT2 = os.path.join(HERE, "lab-setup-run.png")
problems = [f"{os.path.basename(OUT1)}: {p}" for p in p1.s.problems] + \
           [f"{os.path.basename(OUT2)}: {p}" for p in p2.s.problems]
if problems:
    refuse("the pictures have defects:\n  " + "\n  ".join(problems))
tmp1, tmp2 = OUT1 + ".part.png", OUT2 + ".part.png"
p1.s.save(tmp1)                       # save() runs its own checks too, and exits on a defect
try:
    p2.s.save(tmp2)
except SystemExit:
    os.remove(tmp1)
    raise
os.replace(tmp1, OUT1)
os.replace(tmp2, OUT2)
print("Wrote", OUT1, "and", OUT2)

# ------------------------------------------------------------------ alt text
FAULT_TEXT = (f"work-data stops answering for {' or '.join(_seconds(n) for n in STALLS)}, answers after "
              f"{_seconds(SLOWS[0])}, is not running, or sits at an address that does not answer, or "
              f"{_or(OVERLOAD_USERS)} people press Print")
alt1 = alt_text(
    "How the lab is set up",
    parts=["People pressing Print", "Health check", "notice-app", "work-data-app", "H2 database server"],
    steps=[(1, f"notice-app asks work-data-app to make the tickets; work-data-app makes {ROUND_TRIPS} "
               f"round trips per ticket to the H2 database, {LATENCY_MS} milliseconds each"),
           (2, "notice-app asks work-data-app to mark them printed")],
    finding=(f"A load generator (people who give up after {GIVE_UP_S} seconds) and a health check "
             f"{PROBE_TEXT} call notice-app (port {NOTICE_PORT}), which calls work-data-app (port {WORK_PORT}), "
             f"which calls an H2 database server standing in for the shop's Oracle database (port {DB_PORT}). "
             f"For each run, run_lab.py sets switches on notice-app (Java {_or(JAVAS)}, virtual threads on or off, "
             f"time limits {LIMIT_TEXT}, a circuit breaker {BREAKER_TEXT}, a bulkhead of {BULKHEAD_TEXT}) and on "
             f"work-data-app (database pool {_or(POOLS)}, a driver that holds a lock while it waits, PDF-like "
             f"processor work). It causes trouble on purpose: {FAULT_TEXT}. "
             f"It measures prints answered OK per second, how long people waited, health checks answered, "
             f"named errors (time limit HTTP {GAVE_UP_CODE}, breaker or bulkhead HTTP {_or(REFUSED_CODES)}), "
             f"and stuck calls, threads and memory read from both apps {SAMPLE_TEXT}"))
alt2 = alt_text(
    "How each lab test was run",
    steps=[(letter, f"{head}: {' '.join(lines)}") for letter, head, lines, _ in RUN_STEPS],
    finding=(f"run_lab.py does steps A to H for each of its {len(RUNS)} runs. {REPEATED} of the runs are "
             f"repeated {REPEATS[-1]} times and the middle result is reported, with the range; results are "
             f"written to results.json and RESULTS.md"))
for out, alt in ((OUT1, alt1), (OUT2, alt2)):
    print("Wrote", write_alt(out, alt))
    print("Short alt:", alt["short"])
