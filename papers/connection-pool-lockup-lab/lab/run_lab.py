#!/usr/bin/env python3
"""Runs PizzaPoolLab.java on Java 17, Java 21, and Java 21 with virtual threads, then writes
results/results.json, results/RESULTS.md and the raw output of each run (results/<run>.txt).

Finding the JDKs, in this order:
  1. JAVA17_HOME and JAVA21_HOME environment variables
  2. Common install folders (C:\\Program Files\\Java, Eclipse Adoptium, Microsoft, ~/.jdks, ~/tools)
Finding the jars: the local Maven cache (~/.m2). If one is missing, the script prints the
mvn command that downloads it.

Run:  python papers/connection-pool-lockup-lab/lab/run_lab.py [--repeats 3] [-Dpool=10 -Dpizzas=50 ...]
Any -D setting is passed to every run. Each run is repeated (3 times by default) and the
middle result for each scenario is reported, because timings near the pool wait vary a little.
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
SOURCE = os.path.join(HERE, "PizzaPoolLab.java")

JARS = [("com.h2database", "h2", "2.2.224"),
        ("com.zaxxer", "HikariCP", "5.0.1"),
        ("org.slf4j", "slf4j-api", "2.0.18")]

RUNS = [("java-17", "17", "platform"),
        ("java-21", "21", "platform"),
        ("java-21-virtual", "21", "virtual")]


def find_jdk(major):
    env = os.environ.get(f"JAVA{major}_HOME")
    if env and os.path.exists(os.path.join(env, "bin")):
        return env
    home = os.path.expanduser("~")
    patterns = [rf"C:\Program Files\Java\jdk-{major}*", rf"C:\Program Files\Eclipse Adoptium\jdk-{major}*",
                rf"C:\Program Files\Microsoft\jdk-{major}*", os.path.join(home, ".jdks", f"*{major}*"),
                os.path.join(home, "tools", f"jdk-{major}*"), f"/usr/lib/jvm/*{major}*",
                f"/Library/Java/JavaVirtualMachines/*{major}*/Contents/Home"]
    for p in patterns:
        for d in sorted(glob.glob(p), reverse=True):
            if os.path.exists(os.path.join(d, "bin")):
                return d
    return None


def classpath():
    repo = os.path.join(os.path.expanduser("~"), ".m2", "repository")
    paths, missing = [], []
    for group, artifact, version in JARS:
        p = os.path.join(repo, *group.split("."), artifact, version, f"{artifact}-{version}.jar")
        (paths if os.path.exists(p) else missing).append(p if os.path.exists(p) else f"{group}:{artifact}:{version}")
    if missing:
        for m in missing:
            print(f"Missing jar. Download it with:  mvn dependency:get -Dartifact={m}", file=sys.stderr)
        sys.exit(1)
    return os.pathsep.join(paths)


def parse(out):
    """Turns the lab's printed report into {scenario number: figures}."""
    results, current = {}, None
    for line in out.splitlines():
        if m := re.match(r"== (\d+)\. (.*)", line):
            current = m.group(1)
            results[current] = {"title": m.group(2)}
            continue
        if current is None:
            continue
        r = results[current]
        if m := re.search(r"Took ([\d.]+) s\. Longest single request ([\d.]+) s", line):
            r.update(seconds=float(m.group(1)), longest=float(m.group(2)))
        if m := re.search(r"at most (\d+) of (\d+) connections in use, at most (\d+) requests waiting", line):
            r.update(peak_in_use=int(m.group(1)), pool=int(m.group(2)), waiting=int(m.group(3)))
        if m := re.search(r"Requests: (\d+) finished, (\d+) failed, (\d+) till retries, (\d+) of (\d+) people", line):
            r.update(ok=int(m.group(1)), failed=int(m.group(2)), retries=int(m.group(3)),
                     gave_up=int(m.group(4)), staff=int(m.group(5)))
        if m := re.search(r"lost \(error ignored\): (\d+)", line):
            r["lost"] = int(m.group(1))
        if m := re.search(r"The big update took ([\d.]+) s", line):
            r["seconds"] = float(m.group(1))
        if m := re.search(r"kitchen screen waited ([\d.]+) s", line):
            r["kitchen_waited"] = float(m.group(1))
        if m := re.search(r"Result: (\w+)", line):
            r["verdict"] = m.group(1)
    return results


def main():
    args = sys.argv[1:]
    settings = [a for a in args if a.startswith("-D")]
    repeats = int(args[args.index("--repeats") + 1]) if "--repeats" in args else 3
    cp = classpath()
    os.makedirs(RESULTS, exist_ok=True)
    all_results = {"settings": settings, "repeats": repeats, "runs": {}}
    for name, major, threads in RUNS:
        jdk = find_jdk(major)
        if not jdk:
            print(f"{name}: no Java {major} found. Set JAVA{major}_HOME.", file=sys.stderr)
            sys.exit(1)
        java = os.path.join(jdk, "bin", "java")
        print(f"Running {name} ({jdk}), {repeats} times ...", flush=True)
        outputs = []
        for _ in range(repeats):
            out = subprocess.run([java, "-cp", cp, f"-Dthreads={threads}", *settings, SOURCE],
                                 capture_output=True, text=True, timeout=900)
            if out.returncode != 0:
                print(out.stdout + out.stderr, file=sys.stderr)
                sys.exit(out.returncode)
            outputs.append(out.stdout)
        with open(os.path.join(RESULTS, f"{name}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(f"######## Repeat {i + 1} of {repeats}\n{o}" for i, o in enumerate(outputs)))
        version = re.search(r"Java (\S+)", outputs[0]).group(1)
        each = [parse(o) for o in outputs]
        middle = {num: middle_of([e[num] for e in each]) for num in each[0]}
        all_results["runs"][name] = {"java": version, "threads": threads, "scenarios": middle,
                                     "every_repeat": each}
    with open(os.path.join(RESULTS, "results.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=1)
    write_md(all_results)
    print("Wrote results/results.json and results/RESULTS.md")


def middle_of(results):
    """The repeat with the middle time for this scenario."""
    ordered = sorted(results, key=lambda r: r["seconds"])
    return ordered[len(ordered) // 2]


def cell(s):
    if "kitchen_waited" in s:
        return f"{s['verdict']}: kitchen screen waited {s['kitchen_waited']:.1f} of {s['seconds']:.1f} s"
    return (f"{s['verdict']}: {s['seconds']:.1f} s, {s['ok']} of {s['staff']} through, "
            f"{s['lost']} snapshots lost, {s['retries']} retries, {s['gave_up']} gave up")


def write_md(res):
    runs = res["runs"]
    names = list(runs)
    lines = ["# Results", "",
             "Written by `lab/run_lab.py`. Do not edit by hand.", "",
             "Settings: " + (" ".join(res["settings"]) or "the defaults (5 connections, 10 pizzas, 6 people)")
             + f". Each run repeated {res['repeats']} times; the middle result is shown.", "",
             "| Scenario | " + " | ".join(f"{n} (Java {runs[n]['java']}, {runs[n]['threads']} threads)" for n in names) + " |",
             "|---|" + "---|" * len(names)]
    first = runs[names[0]]["scenarios"]
    for num in first:
        row = [f"{num}. {first[num]['title']}"] + [cell(runs[n]["scenarios"][num]) for n in names]
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "Raw output: " + ", ".join(f"[{n}.txt]({n}.txt)" for n in names), ""]
    with open(os.path.join(RESULTS, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
