# CLAUDE.md: rules for this repository

These rules are for anyone adding to this repository, person or AI agent. Read them before you
write or move anything. `python tools/check_papers.py` checks most of them.

## 1. This repository is public: keep it anonymous

- **Never name a real client, agency, company, team, system, product, ticket or person.** That
  includes names in code comments, file names, commit messages, results files and picture text.
- **Use the made-up pizza shop instead.** Describe the shape of the problem, not where it came
  from. A real "service that prints notices" becomes "the ticket service that prints kitchen
  tickets". Keep every number and finding; change only the names.
- **The pizza shop's parts** (use these so papers read as one world):

  | Pizza shop part | Use it for |
  |---|---|
  | The till | Any front-end or caller app that staff use |
  | The order service | A back-end service that saves orders and order lines |
  | The order-data service | A service that reads and writes the shop's data for another service |
  | The ticket service | A service that makes printed documents (kitchen tickets) |
  | The kitchen screen | A second app that changes the same data |
  | The shop's database | The production database |
  | Pizzas on an order | Lines on a record (an order with 1,000 pizzas = a record with 1,000 lines) |
  | The front door | The gateway that sits in front of the services |

- **No authors by name.** Write `**Prepared by:** the engineering team`.
- **No real data.** Every value in a lab, a result or a picture is made up.
- **Real vendor and open-source names are fine:** Java, Spring Boot, Oracle, H2, HikariCP,
  Resilience4j, Tomcat, AWS, Salesforce, Claude Code and so on.
- The private word list is `tools/private-terms.txt`. It is in `.gitignore` and must **never** be
  committed, because the list itself would name the client. Each person keeps their own copy.
  If you don't have it, ask the repository owner.

## 2. One folder per paper

```
papers/<paper-name>/
├── README.md        the paper
├── assets/          pictures + their .png.alt.md + the script that draws them
├── lab/             runnable code (optional)
├── results/         lab output (optional)
└── exports/         Word or PDF copies and the script that builds them (optional)
```

- The paper is always `README.md`, so GitHub shows it when the folder opens.
- A second document for the same paper (an executive brief, a slide outline) sits beside it with
  a plain name: `executive-brief.md`.
- Nothing loose in `papers/`. Out-of-date papers move whole to `archive/<paper-name>/`, and
  their header says `**Status:** Archived` with a line saying what replaced them.
- Shared code (the diagram toolkit, the checker) lives in `tools/`. A paper may use it through a
  relative path; it must not reach outside the repository.

## 3. Names

| What | Rule | Example |
|---|---|---|
| Paper folder | lowercase, hyphens, says what it's about, no date, no version | `connection-pool-lockup-lab` |
| Other files | lowercase, hyphens | `pool-problem-and-fix.png`, `build_pool_problem.py` |
| Code | the language's own rules | `PizzaPoolLab.java`, `run_lab.py` |
| Standard files | as usual | `README.md`, `RESULTS.md`, `CLAUDE.md`, `SKILL.md` |
| Word or PDF copy | `<paper-name>-v<version>.<ext>` | `printing-hang-fixes-compared-v1.7.docx` |
| Picture description | the picture's name + `.alt.md` | `pool-problem-and-fix.png.alt.md` |

Endings that say what the paper is: `-lab` (we tested it), `-compared` (we compared options),
`-case-study` (what happened on a real piece of work), `-guide` (how to do something).

## 4. The header block

Every paper starts like this. The checker looks for each line.

```markdown
# Title that says the finding or the question

## One-line subtitle

**Classification:** Internal: Engineering Reference
**Prepared by:** the engineering team
**Date:** YYYY-MM-DD
**Version:** 1.0
**Status:** Draft | Proposal | Published | Archived
```

Optional lines after these: `**Lab code:**`, `**Results:**`, `**Related:**` (links to other
papers in this repository only).

**Versions:** add 0.1 for a correction or new finding; go to the next whole number when the
paper is restructured or its conclusion changes. Update the date and the export file name at the
same time. Git keeps the history, so don't keep old copies.

## 5. Writing

- **Plain, everyday English.** The test: a junior developer, new to the subject, reads it once
  and has no follow-up questions. Define a technical term in brackets the first time it appears.
- **Lead with the answer.** Every paper opens with an "In short" list of the findings.
- **Short sentences and short bullets.** No walls of text.
- **Every number comes from a run.** Say which run, how many repeats, and where the raw output is.
- **Say what the paper doesn't show.** Every lab paper has a "What this doesn't show" section.
- **Labels are prose too.** Table headers, picture boxes and chart legends follow the same rules.
  Never use a bare code or abbreviation as a label: write what it means first.

## 6. Pictures

- Drawn by a script in the paper's `assets/` folder, from the lab's results files, never by hand
  and never with numbers typed in. The picture's footer names the script.
- Use `tools/diagrams/` (`slide_kit.py`). Colours are cyan, yellow and magenta, never red and
  green as the only difference, and words always carry the meaning as well as colour.
- Every `.png` has a `.png.alt.md` with a short and a long description. The paper's picture link
  has the long description as its alt text.

## 7. Labs

- Runnable on a laptop with nothing but the tools listed in the paper's "Run it yourself"
  section. No servers, no real databases, no private network.
- One command runs everything and writes `results/RESULTS.md` and `results/results.json`.
- Repeat timing runs (3 is the default) and report the middle result.
- Threads in a lab are test scaffolding. A paper must not recommend hand-made thread pools or
  thread code as a fix; recommend configuration, platform features or design changes.
- Logs and build output (`target/`, `results/logs/`) are not committed.

## 8. Before you commit

1. `python tools/check_papers.py` passes.
2. The table in the top-level `README.md` lists the paper.
3. Search for merge-conflict markers (`<<<<<<<`, `>>>>>>>`), because more than one session may
   edit this repository.
4. Commit messages say what changed and why. No personal names, no AI attribution lines, no client
   names.
5. Work on `feature/*` branches and merge to `main` through a pull request.

## 9. Skills

Step-by-step guides in `.claude/skills/`:

- `new-white-paper`: start a paper from the template.
- `anonymise-paper`: turn a real-world write-up into the pizza shop before it comes in.
- `lab-paper`: build a runnable lab, its results and its pictures.
- `publish-paper`: final checks, the Word copy, and the commit.
