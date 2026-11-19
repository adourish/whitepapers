#!/usr/bin/env python3
"""Runs every experiment in the Java 17 or Java 21 lab and writes results/results.json and
results/RESULTS.md. Each run starts a fresh database and a fresh pair of apps, warms them up, then
measures. Most runs are repeated 3 times and the middle result is reported, with the range.

    python run_lab.py                 # every run (about 90 minutes)
    python run_lab.py stall pin       # only runs whose name contains one of these words

Set JDK17 and JDK21 to the JDK folders if they are not where this machine keeps them.
"""
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
JDK17 = os.environ.get("JDK17", os.path.expanduser(r"~\tools\jdk-17.0.21+9"))
JDK21 = os.environ.get("JDK21", r"C:\Program Files\Java\jdk-21.0.12.1")
H2_JAR = os.path.expanduser(r"~\.m2\repository\com\h2database\h2\2.2.224\h2-2.2.224.jar")
WD_JAR = os.path.join(HERE, "work-data-app", "target", "work-data-app-1.0.0.jar")
NS_JAR = os.path.join(HERE, "notice-app", "target", "notice-app-1.0.0.jar")
LOGS = os.path.join(HERE, "results", "logs")
PRINT = "http://localhost:18084/notice/api/generatePrintNotices?notices=5"
PING = "http://localhost:18084/notice/api/ping"
STATS = "http://localhost:18084/admin/stats,http://localhost:18093/admin/stats"

# Option A of the change request: 2 seconds to connect, 30 seconds to answer (developer-kit/option-a-every-waited-call)
OPTION_A = {"lab.client.connect-timeout-ms": 2000, "lab.client.read-timeout-ms": 30000}
LIMIT_10 = {"lab.client.connect-timeout-ms": 2000, "lab.client.read-timeout-ms": 10000}
INLINE = {"lab.workdata.mode": "inline"}
CPU = {"lab.workdata.mode": "inline", "spring.datasource.hikari.maximum-pool-size": 100, "lab.cpu.kb-per-notice": 2000}
ZGC = ["-XX:+UseZGC", "-XX:+ZGenerational"]


def run(name, what, jdk=17, virtual=False, wd=None, ns=None, users=40, seconds=30, timeout=29, stall=None,
        down=False, blackhole=False, sessions=None, gc=None, repeats=1, series=None, wd_jdk=None, wd_virtual=None,
        trace=True):
    return dict(name=name, what=what, jdk=jdk, virtual=virtual, wd=wd or {}, ns=ns or {}, users=users,
                seconds=seconds, timeout=timeout, stall=stall, down=down, blackhole=blackhole, sessions=sessions,
                gc=gc or [], repeats=repeats, series=series or [], wd_jdk=wd_jdk or jdk,
                wd_virtual=virtual if wd_virtual is None else wd_virtual, trace=trace)


V = dict(jdk=21, virtual=True)
LONG = ["notice.inFlight", "notice.heapUsedMb", "notice.platformThreads"]
RUNS = [
    # A. Does Java 21 on its own make the waiting path faster?
    run("normal-17", "Normal load, 40 people", repeats=3),
    run("normal-21", "Normal load, 40 people", jdk=21, repeats=3),
    run("normal-21-virtual", "Normal load, 40 people", **V, repeats=3),
    # B. Do virtual threads get past printNoticeExecutor?
    run("overload-17", "150 people: more than printNoticeExecutor holds", users=150, repeats=3),
    run("overload-21-virtual", "150 people: more than printNoticeExecutor holds", users=150, **V, repeats=3),
    # C, D. Work-data stops answering, with and without the change request's limits
    run("stall-no-limit-17", "Work-data stops answering; no limit (today)", users=300, seconds=40, stall="hang", repeats=3),
    run("stall-no-limit-21-virtual", "Work-data stops answering; no limit (today)", users=300, seconds=40, stall="hang", **V, repeats=3),
    run("stall-option-a-17", "Work-data stops answering; option A limits (30 s)", users=300, seconds=40, stall="hang", ns=OPTION_A, repeats=3),
    run("stall-option-a-21-virtual", "Work-data stops answering; option A limits (30 s)", users=300, seconds=40, stall="hang", ns=OPTION_A, **V, repeats=3),
    # E. Work-data is slow (20 s) but answers: do the limits turn slow work into errors?
    run("slow-option-a-17", "Work-data answers after 20 s; option A limits (30 s)", users=60, seconds=45, stall="slow:20000", ns=OPTION_A, repeats=3),
    run("slow-option-a-21-virtual", "Work-data answers after 20 s; option A limits (30 s)", users=60, seconds=45, stall="slow:20000", ns=OPTION_A, **V, repeats=3),
    run("slow-limit-10-17", "Work-data answers after 20 s; a 10 s limit (too short)", users=60, seconds=45, stall="slow:20000",
        ns={"lab.client.connect-timeout-ms": 2000, "lab.client.read-timeout-ms": 10000}),
    # F, G. Work-data is down, or the network drops the connection attempt
    run("down-option-a-17", "Work-data is not running; option A limits", users=50, seconds=20, down=True, ns=OPTION_A),
    run("unreachable-no-limit-17", "Work-data's address does not answer at all; no connect limit", users=50, seconds=30, blackhole=True),
    run("unreachable-option-a-17", "Work-data's address does not answer at all; 2 s connect limit", users=50, seconds=30, blackhole=True, ns=OPTION_A),
    # H. A 5-minute stall: do stuck calls keep piling up?
    run("long-stall-no-limit-17", "5-minute stall; no limit", users=300, seconds=300, stall="hang", series=LONG),
    run("long-stall-no-limit-21-virtual", "5-minute stall; no limit", users=300, seconds=300, stall="hang", series=LONG, **V),
    run("long-stall-option-a-21-virtual", "5-minute stall; option A limits", users=300, seconds=300, stall="hang", ns=OPTION_A, series=LONG, **V),
    # I. Partial rollout: notice on Java 21 virtual, work-data still on Java 17
    run("mixed-normal", "Notice on 21 virtual, work-data on 17; normal load", **V, wd_jdk=17, wd_virtual=False, repeats=3),
    run("mixed-stall-option-a", "Notice on 21 virtual, work-data on 17; work-data stops answering; option A",
        users=300, seconds=40, stall="hang", ns=OPTION_A, **V, wd_jdk=17, wd_virtual=False),
    # J. Database pool size when the database itself can only work on 40 calls at once
    run("dbcap40-pool25-17", "No executor; database works on 40 at once; pool 25", users=200, timeout=60, sessions=40, wd=INLINE),
    run("dbcap40-pool25-21-virtual", "No executor; database works on 40 at once; pool 25", users=200, timeout=60, sessions=40, wd=INLINE, **V, repeats=3),
    run("dbcap40-pool50-21-virtual", "No executor; database works on 40 at once; pool 50", users=200, timeout=60, sessions=40,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 50}, **V, repeats=3),
    run("dbcap40-pool100-21-virtual", "No executor; database works on 40 at once; pool 100", users=200, timeout=60, sessions=40,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100}, **V, repeats=3),
    # K. Pinning: a driver that holds a lock while it waits, as older Oracle drivers do
    run("pin-off-21-virtual", "No executor, pool 100; driver without a lock", users=200,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100}, **V, repeats=3, trace=False),
    run("pin-on-21-virtual", "No executor, pool 100; driver holds a lock while it waits", users=200,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100, "lab.db.hold-lock": "true"}, **V, repeats=3, trace=False),
    run("pin-on-17", "No executor, pool 100; driver holds a lock while it waits", users=200,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100, "lab.db.hold-lock": "true"}),
    run("pin-on-21-virtual-traced", "As pin-on, with the pinning trace on (counts reports)", users=50, seconds=10,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100, "lab.db.hold-lock": "true"}, **V),
    # L. Processor-heavy work, shaped like making PDFs
    run("cpu-17", "PDF-like processor work, 100 people; G1 collector", users=100, wd=CPU, repeats=3),
    run("cpu-21", "PDF-like processor work, 100 people; G1 collector", users=100, wd=CPU, jdk=21, repeats=3),
    run("cpu-21-zgc", "PDF-like processor work, 100 people; generational ZGC", users=100, wd=CPU, jdk=21, gc=ZGC, repeats=3),
    run("cpu-21-virtual", "PDF-like processor work, 100 people; G1, virtual threads", users=100, wd=CPU, **V, repeats=3),
    # M. HTTP client pools
    run("httppool-simple-21-virtual", "HTTP client: today's simple client", users=100,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100}, **V),
    run("httppool-default-21-virtual", "HTTP client: Apache pool at its defaults (5 per address)", users=100,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100}, ns={"lab.client.kind": "pooled"}, **V),
    run("httppool-100-21-virtual", "HTTP client: Apache pool, 100 per address", users=100,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100},
        ns={"lab.client.kind": "pooled", "lab.client.pool.max-total": 100, "lab.client.pool.max-per-route": 100}, **V),
    # N. Fill in the white paper's table: each scenario with and without limits, on both versions
    run("fill-normal-option-a-17", "Normal load, 40 people; option A limits", ns=OPTION_A, repeats=3),
    run("fill-normal-option-a-21-virtual", "Normal load, 40 people; option A limits", ns=OPTION_A, **V, repeats=3),
    run("fill-overload-option-a-17", "150 people; option A limits", users=150, ns=OPTION_A, repeats=3),
    run("fill-overload-option-a-21-virtual", "150 people; option A limits", users=150, ns=OPTION_A, **V, repeats=3),
    run("fill-stall-limit-10-17", "Work-data stops answering; 10 s read limit", users=300, seconds=40, stall="hang", ns=LIMIT_10, repeats=3),
    run("fill-stall-limit-10-21-virtual", "Work-data stops answering; 10 s read limit", users=300, seconds=40, stall="hang", ns=LIMIT_10, **V, repeats=3),
    run("fill-long-stall-option-a-17", "5-minute stall; option A limits", users=300, seconds=300, stall="hang", ns=OPTION_A, series=LONG),
    run("fill-slow-no-limit-17", "Work-data answers after 20 s; no limit", users=60, seconds=45, stall="slow:20000", repeats=3),
    run("fill-slow-no-limit-21-virtual", "Work-data answers after 20 s; no limit", users=60, seconds=45, stall="slow:20000", **V, repeats=3),
    run("fill-slow-limit-10-21-virtual", "Work-data answers after 20 s; a 10 s limit (too short)", users=60, seconds=45, stall="slow:20000", ns=LIMIT_10, **V),
    run("fill-down-no-limit-17", "Work-data is not running; no limit", users=50, seconds=20, down=True),
    run("fill-down-no-limit-21-virtual", "Work-data is not running; no limit", users=50, seconds=20, down=True, **V),
    run("fill-down-option-a-21-virtual", "Work-data is not running; option A limits", users=50, seconds=20, down=True, ns=OPTION_A, **V),
    run("fill-unreachable-no-limit-21-virtual", "Work-data's address does not answer at all; no connect limit", users=50, seconds=30, blackhole=True, **V),
    run("fill-unreachable-option-a-21-virtual", "Work-data's address does not answer at all; 2 s connect limit", users=50, seconds=30, blackhole=True, ns=OPTION_A, **V),
    run("fill-pin-on-option-a-17", "No executor, pool 100; driver holds a lock; option A limits", users=200,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100, "lab.db.hold-lock": "true"}, ns=OPTION_A),
    run("fill-pin-on-option-a-21-virtual", "No executor, pool 100; driver holds a lock; option A limits", users=200,
        wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100, "lab.db.hold-lock": "true"}, ns=OPTION_A, **V, repeats=3, trace=False),
    run("fill-cpu-option-a-17", "PDF-like processor work, 100 people; option A limits", users=100, wd=CPU, ns=OPTION_A),
    run("fill-cpu-option-a-21-virtual", "PDF-like processor work, 100 people; option A limits", users=100, wd=CPU, ns=OPTION_A, **V),
    run("fill-mixed-stall-no-limit", "Notice on 21 virtual, work-data on 17; work-data stops answering; no limit",
        users=300, seconds=40, stall="hang", **V, wd_jdk=17, wd_virtual=False),
]

# O. The five options, each across the same nine scenarios. Options a (Java 17, no changes) and b (Java 17, MVP
# limits) are already covered above; these add c, d, e, and Java 17 with the circuit breaker.
SCENARIOS = {
    "normal": dict(what="Normal load, 40 people", repeats=3),
    "overload": dict(what="150 people", users=150, repeats=3),
    "stall": dict(what="Work-data stops answering", users=300, seconds=40, stall="hang", repeats=3),
    "long-stall": dict(what="5-minute stall", users=300, seconds=300, stall="hang", series=LONG),
    "slow": dict(what="Work-data answers after 20 s", users=60, seconds=45, stall="slow:20000", repeats=3),
    "down": dict(what="Work-data is not running", users=50, seconds=20, down=True),
    "unreachable": dict(what="Work-data's address does not answer at all", users=50, seconds=30, blackhole=True),
    "pin": dict(what="No executor, pool 100; driver holds a lock", users=200,
                wd={**INLINE, "spring.datasource.hikari.maximum-pool-size": 100, "lab.db.hold-lock": "true"}),
    "cpu": dict(what="PDF-like processor work, 100 people", users=100, wd=CPU),
}
BREAKER = {"lab.client.breaker": "true"}
OPTIONS = {
    "opt-c": ("Java 21, no changes", dict(jdk=21), {}),
    "opt-d": ("Java 21, MVP limits", dict(jdk=21), OPTION_A),
    "opt-e": ("Java 21 virtual, MVP limits, circuit breaker", dict(jdk=21, virtual=True, trace=False), {**OPTION_A, **BREAKER}),
}
for key, (label, jvm, ns) in OPTIONS.items():
    for sc, args in SCENARIOS.items():
        args = dict(args)
        what = "%s; %s" % (args.pop("what"), label)
        RUNS.append(run("%s-%s" % (key, sc), what, ns=ns, **jvm, **args))
for sc in ("normal", "stall", "long-stall", "slow", "overload"):
    args = dict(SCENARIOS[sc])
    what = "%s; Java 17, MVP limits, circuit breaker" % args.pop("what")
    RUNS.append(run("opt-b-breaker-%s" % sc, what, ns={**OPTION_A, **BREAKER}, **args))
# The breaker above counts work-data's "too busy" refusals as failures, so overload opens it. These count only
# time-outs and failed connections.
BREAKER_TIMEOUTS = {**BREAKER, "lab.client.breaker.record": "timeouts"}
for sc in ("overload", "stall", "long-stall", "slow"):
    for key, label, jvm in (("opt-b-breaker-timeouts", "Java 17", {}),
                            ("opt-e-timeouts", "Java 21 virtual", dict(jdk=21, virtual=True, trace=False))):
        args = dict(SCENARIOS[sc])
        what = "%s; %s, MVP limits, circuit breaker counting only time-outs" % (args.pop("what"), label)
        RUNS.append(run("%s-%s" % (key, sc), what, ns={**OPTION_A, **BREAKER_TIMEOUTS}, **jvm, **args))
# Bulkhead: at most 50 calls to work-data in progress at once, so a stall can hold at most 50 of Tomcat's 200 threads
BULKHEAD = {**BREAKER_TIMEOUTS, "lab.client.bulkhead": 50}
for sc in ("normal", "overload", "stall", "long-stall", "slow"):
    args = dict(SCENARIOS[sc])
    what = "%s; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 50" % args.pop("what")
    RUNS.append(run("opt-b-bulkhead-%s" % sc, what, ns={**OPTION_A, **BULKHEAD}, **args))
# A cap of 50 is below the 55 calls work-data takes at once, so it refuses some good prints. Try 60.
for sc in ("normal", "overload", "stall", "long-stall", "slow", "down", "unreachable", "pin", "cpu"):
    args = dict(SCENARIOS[sc])
    what = "%s; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60" % args.pop("what")
    RUNS.append(run("opt-b-bulkhead60-%s" % sc, what, ns={**OPTION_A, **BULKHEAD, "lab.client.bulkhead": 60}, **args))
for sc in ("down", "unreachable", "pin", "cpu"):
    args = dict(SCENARIOS[sc])
    what = "%s; Java 17, MVP limits, circuit breaker counting only time-outs" % args.pop("what")
    RUNS.append(run("opt-b-breaker-timeouts-%s" % sc, what, ns={**OPTION_A, **BREAKER_TIMEOUTS}, **args))


def java(jdk):
    return os.path.join(JDK17 if jdk == 17 else JDK21, "bin", "java.exe")


def get(url, timeout=3):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode()


def post(url):
    urllib.request.urlopen(urllib.request.Request(url, method="POST"), timeout=5).read()


def wait_for(url, seconds=60):
    end = time.time() + seconds
    while time.time() < end:
        try:
            get(url, 2)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("did not start: " + url)


def start(jdk, jar, virtual, props, gc, trace, log):
    cmd = [java(jdk), "-Xmx1g"] + (gc if jdk == 21 else [])
    if virtual and trace:
        cmd.append("-Djdk.tracePinnedThreads=short")
    cmd += ["-jar", jar, "--spring.threads.virtual.enabled=%s" % str(virtual).lower()]
    cmd += ["--%s=%s" % kv for kv in props.items()]
    return subprocess.Popen(cmd, stdout=open(log, "w"), stderr=subprocess.STDOUT)


def pinned(log):
    with open(log, errors="replace") as f:
        return f.read().count("<== monitors")


def load(c, users, seconds, out):
    cmd = [java(21), os.path.join(HERE, "loadtest", "LoadTest.java"), "--url", PRINT, "--users", str(users),
           "--seconds", str(seconds), "--timeout", str(c["timeout"]), "--probe", PING, "--stats", STATS,
           "--series", ",".join(c["series"]) or "none", "--out", out]
    subprocess.run(cmd, check=True, timeout=seconds + c["timeout"] + 120, stdout=subprocess.DEVNULL)
    return json.load(open(out))


def one(c, rep):
    tag = "%s-%d" % (c["name"], rep)
    wd_log, ns_log = os.path.join(LOGS, tag + "-work-data.log"), os.path.join(LOGS, tag + "-notice.log")
    h2_cmd = [java(17)] + (["-Dlab.db.sessions=%d" % c["sessions"]] if c["sessions"] else [])
    h2_cmd += ["-cp", H2_JAR + os.pathsep + os.path.join(HERE, "work-data-app", "target", "classes"),
               "org.h2.tools.Server", "-tcp", "-tcpPort", "19092", "-ifNotExists"]
    procs = [subprocess.Popen(h2_cmd, stdout=open(os.path.join(LOGS, tag + "-h2.log"), "w"), stderr=subprocess.STDOUT)]
    try:
        time.sleep(2)
        ns = dict(c["ns"])
        if c["blackhole"]:
            ns["lab.work-data.url"] = "http://10.255.255.1:18093"   # an address nothing answers
        if not c["down"]:
            procs.append(start(c["wd_jdk"], WD_JAR, c["wd_virtual"], c["wd"], c["gc"], c["trace"], wd_log))
            wait_for("http://localhost:18093/api/ping")
        procs.append(start(c["jdk"], NS_JAR, c["virtual"], ns, c["gc"], c["trace"], ns_log))
        wait_for(PING)
        if not (c["down"] or c["blackhole"]):
            load(c, 5, 8, os.path.join(LOGS, tag + "-warmup.json"))      # warm-up, not counted
        if c["stall"] == "hang":
            post("http://localhost:18093/admin/stall?on=true")
        elif c["stall"] and c["stall"].startswith("slow:"):
            post("http://localhost:18093/admin/stall?on=true&ms=" + c["stall"][5:])
        r = load(c, c["users"], c["seconds"], os.path.join(LOGS, tag + ".json"))
    finally:
        for p in procs:
            p.kill()
        for p in procs:
            p.wait()
    r["pinned"] = (pinned(wd_log) if os.path.exists(wd_log) else 0) + pinned(ns_log)
    return r


def main():
    want = sys.argv[1:]
    runs = [c for c in RUNS if not want or any(w in c["name"] for w in want)]
    os.makedirs(LOGS, exist_ok=True)
    out_path = os.path.join(HERE, "results", "results.json")
    results = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for c in runs:
        reps = []
        for rep in range(1, c["repeats"] + 1):
            print("==", c["name"], rep, flush=True)
            reps.append(one(c, rep))
            time.sleep(2)
        results[c["name"]] = {"config": c, "repeats": reps}
        json.dump(results, open(out_path, "w"), indent=1)
    write_md(results)


def mid(reps):
    """The repeat with the middle throughput, and the range of throughput across repeats."""
    s = sorted(reps, key=lambda r: r["okPerSecond"])
    return s[len(s) // 2], (s[0]["okPerSecond"], s[-1]["okPerSecond"])


def write_md(results):
    rows = ["| Run | What it tests | Java | Threads | Repeats | Answered OK a second (range) | Middle wait (ms) "
            "| Slowest 1 in 20 (ms) | Other outcomes, middle repeat | Pings answered | Peak calls stuck in notice "
            "| Peak notice memory (MB) | Peak DB connections in use | Pinned-thread reports |",
            "|---|---|---|---|---:|---|---:|---:|---|---|---:|---:|---:|---:|"]
    for name, res in results.items():
        c, reps = res["config"], res["repeats"]
        r, (lo, hi) = mid(reps)
        p = r.get("peaks", {})
        other = ", ".join("%s: %s" % kv for kv in r["outcomes"].items() if kv[0] != "HTTP 200") or "none"
        java_ = "%s" % c["jdk"] + ("" if c["wd_jdk"] == c["jdk"] else " (work-data %s)" % c["wd_jdk"])
        threads = ("virtual" if c["virtual"] else "platform") + (" + ZGC" if c["gc"] else "")
        rng = "%s (%s to %s)" % (r["okPerSecond"], lo, hi) if len(reps) > 1 else str(r["okPerSecond"])
        rows.append("| `%s` | %s | %s | %s | %d | %s | %s | %s | %s | %s of %s | %s | %s | %s | %s |" % (
            name, c["what"], java_, threads, len(reps), rng, r["p50"], r["p95"], other, r["probeOk"],
            r["probeOk"] + r["probeFail"], p.get("notice.peakInFlight", "-"), p.get("notice.heapUsedMb", "-"),
            p.get("workData.peakPoolActive", "-"), r["pinned"]))
    long_rows = []
    for name, res in results.items():
        s = res["repeats"][0].get("series", {}).get("notice.inFlight")
        if s:
            long_rows.append("| `%s` | %s |" % (name, ", ".join(str(v) for v in s[::15])))
    with open(os.path.join(HERE, "results", "RESULTS.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Lab results, round 2\n\nWritten by `run_lab.py`; do not edit by hand. -1 means no request "
                "finished. A person who gets an error waits 1 second before pressing Print again.\n\n"
                + "\n".join(rows) + "\n")
        if long_rows:
            f.write("\n## Calls stuck in the ticket service (notice-app) during the 5-minute stalls, every 30 seconds\n\n"
                    "| Run | Stuck calls |\n|---|---|\n" + "\n".join(long_rows) + "\n")


if __name__ == "__main__":
    main()
