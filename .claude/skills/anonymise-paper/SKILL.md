---
name: anonymise-paper
description: Turn a real-world finding, incident or analysis into the made-up pizza shop before it goes into this public repository. Use whenever a paper, lab or picture starts from real client work.
---

# Anonymise a paper (the pizza shop)

This repository is public. Nothing may name a real client, system, team, ticket or person.

1. **List every real name** in the source: organisations, systems, services, databases, schemas,
   tables, fields, repositories, branches, ticket keys, client release numbers, server names,
   people.
2. **Map each one to the pizza shop** using the table in CLAUDE.md section 1. Keep the mapping
   the same all through the paper. Invent sensible names for anything not in the table (for
   example, a firm lookup becomes "the supplier lookup").
3. **Keep the shape and the numbers.** Change names only. If a number would identify the client
   (a count of their customers, a release date), round it or describe it instead.
4. **Rename inside the code too:** table and column names, class names, log text, comments,
   property keys, pool names and test data. A lab should read as if it was always about pizzas.
5. **Leave out anything that can't be anonymised:** screenshots, real logs, real query output,
   security findings. Describe them in words, or drop them.
6. **Check:** run `python tools/check_papers.py`. It reads `tools/private-terms.txt`, which is
   never committed. Add any new real names from step 1 to that file, so the next check catches them.
7. Tell the person what you changed and anything you left out.
