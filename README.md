# White Papers

Engineering white papers, lab tests and comparisons. Each paper explains one question in plain
language, shows how it was tested, and keeps the code and results next to it so anyone can run
it again.

Every example uses a **made-up pizza shop**. No paper names a real client, system or person.

## The papers

| Paper | What it answers | Lab code | Status |
|---|---|---|---|
| [When one request needs two connections](papers/connection-pool-lockup-lab/) | Why a database connection pool locks up, and whether Java 21 helps (it doesn't) | Yes, Java 17 and 21 | Published |
| [Stopping the kitchen ticket hang](papers/printing-hang-fixes-compared/) | Seven ways to stop a service hanging when the service it calls stops answering: Java 21, time limits, circuit breakers and bulkheads | Yes, Java 17 and 21 | Published |
| [AI coding tools compared](papers/ai-coding-tools-compared/) | Which AI coding assistant to choose, with an executive brief | No | Proposal |
| [AI testing tools compared](papers/ai-testing-tools-compared/) | Which browser automation and testing tools work best with an AI coding assistant | No | Proposal |
| [Agentic engineering case study](papers/agentic-engineering-migration-case-study/) | How a team of AI agents moved a full data model in 58 hours | No | Published |

## How the repository is laid out

```
whitepapers/
├── README.md                 this page: the list of papers
├── CLAUDE.md                 the rules, for people and AI agents
├── papers/                   one folder per paper
│   └── <paper-name>/
│       ├── README.md         the paper itself (GitHub shows it when you open the folder)
│       ├── assets/           pictures, each with a .png.alt.md description and the script that draws it
│       ├── lab/              code that can be run again (only if the paper tests something)
│       ├── results/          what the lab wrote out (only if there is a lab)
│       └── exports/          Word or PDF copies, and the script that makes them
├── archive/                  papers that are out of date, same layout
├── templates/                starting points for a new paper
├── tools/
│   ├── check_papers.py       checks layout, names, links, pictures and private words
│   └── diagrams/             the toolkit the picture scripts use
└── .claude/skills/           step-by-step guides an AI agent follows
```

## Adding a paper

1. Copy `templates/paper/` to `papers/<paper-name>/` (lowercase, hyphens, no date, no version).
2. Write the paper in its `README.md`. Fill in the header block.
3. Put code in `lab/`, results in `results/`, pictures in `assets/`.
4. Add a row to the table above.
5. Run `python tools/check_papers.py`. It must pass before you commit.

The full rules are in [CLAUDE.md](CLAUDE.md).

## Licence

Apache 2.0. See [LICENSE](LICENSE).
