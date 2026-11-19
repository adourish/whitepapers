---
name: lab-paper
description: Build a runnable lab for a white paper, with repeat runs, results files and pictures drawn from those results. Use when a paper tests or measures something.
---

# Build a lab for a paper

1. **Keep it laptop-sized.** Prefer one Java file run with `java File.java`, or a small Maven
   project, with an in-memory database (H2) in place of a real one. No servers, no private network.
2. **Scale the waits down** so a run takes minutes, and say in the paper what was scaled.
3. **Make every setting a `-D` switch** with a sensible default. Print the settings and the Java
   version at the start of each run.
4. **Write one runner** (`lab/run_lab.py`) that:
   - finds each JDK it needs (environment variables such as `JAVA17_HOME` first, then common
     install folders; never a path with a person's user name in it),
   - runs every option the paper compares, repeats each one (3 times by default) and keeps the
     middle result,
   - writes `results/results.json`, `results/RESULTS.md` and the raw output of every run.
5. **Include controls:** scenarios where nothing should go wrong, so a problem scenario means
   something.
6. **Print a clear verdict for each scenario** (OK, BUSY, PROBLEM, BLOCKED), worked out from the
   counts, never typed in.
7. **Draw pictures from `results.json`** with a script in `assets/` that uses
   `tools/diagrams/slide_kit.py`. The script refuses to save if a figure is missing. Write the
   `.png.alt.md` beside each picture.
8. **Threads are scaffolding.** Use them to make people act at the same time. Never recommend
   hand-made threading as the fix.
9. Fill the paper's "Results", "What this doesn't show" and "Run it yourself" sections from the
   actual run, then run `python tools/check_papers.py`.

Example: `papers/connection-pool-lockup-lab/`.
