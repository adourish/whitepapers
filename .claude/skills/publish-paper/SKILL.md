---
name: publish-paper
description: Final checks before a white paper is committed or shared, including the Word copy and the commit. Use when asked to publish, finish, export or commit a paper.
---

# Publish a paper

1. Run `python tools/check_papers.py`. Fix everything. Never commit with failures.
2. Read the paper once as a newcomer. Does "In short" give the answer? Is every term defined the
   first time? Does every number say where it came from?
3. If the lab or pictures changed, run them again so the text, the results and the pictures agree.
4. Set `**Status:** Published`, today's date and the new version (CLAUDE.md section 4).
5. **Word copy (optional):** put a `build_word.py` in `exports/` (copy the one in
   `papers/printing-hang-fixes-compared/exports/`, which uses pandoc and python-docx). Name the
   output `<paper-name>-v<version>.docx` and delete the previous version's file.
6. Update the papers table in the top-level `README.md`.
7. Search for merge-conflict markers: `git grep -n -E "^(<<<<<<<|>>>>>>>)"`.
8. Commit on a `feature/*` branch. The message says what changed and why, with no personal names,
   no client names and no AI attribution lines. Push only when asked.
