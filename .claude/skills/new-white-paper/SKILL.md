---
name: new-white-paper
description: Start a new white paper in this repository from the template, with the right folder, name and header. Use when asked to write, start or add a white paper.
---

# Start a new white paper

1. **Pick the folder name:** lowercase, hyphens, what it's about, no date, no version. End with
   `-lab`, `-compared`, `-case-study` or `-guide` (CLAUDE.md section 3). Check `papers/` and
   `archive/` for a paper on the same question first. If one exists, update it and raise its
   version instead.
2. **Copy the template:** `templates/paper/` to `papers/<paper-name>/`. Delete `lab/` and
   `results/` if the paper tests nothing.
3. **If the material came from real work, anonymise it first** with the `anonymise-paper` skill.
   Nothing from a real client goes in, not even in a first draft.
4. **Fill the header block:** `Prepared by: the engineering team`, today's date, version 0.1,
   status Draft.
5. **Write "In short" first:** the problem, the finding with its number, what to do.
6. If there is a lab, follow the `lab-paper` skill.
7. Add a row to the papers table in the top-level `README.md`.
8. Run `python tools/check_papers.py` and fix everything it reports.
