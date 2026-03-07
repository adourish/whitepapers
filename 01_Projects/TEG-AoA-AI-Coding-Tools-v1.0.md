# TEG One-Pager: AI Coding Assistant Tool Selection — Analysis of Alternatives

**Date:** 2026-03-07
**Author:** REI Systems Engineering
**Status:** Proposal

---

## Executive Summary

Seven AI coding assistant platforms were evaluated across performance, reliability, browser automation, FedRAMP compliance, agentic capability, and cost. The field splits cleanly into two decision contexts: **standard development environments** and **FedRAMP-regulated government networks**.

### Key Takeaways

1. **The full dev loop is the primary selection criterion.** The ability to write code, run an API, open a browser, test the UI, identify issues, and fix them — all in a single uninterrupted agentic session — is the highest-value capability evaluated. Only **Claude Code** and **Devin** complete this loop autonomously and reliably. Cursor and Windsurf Pro handle code + terminal testing well and **CAN open a browser via Playwright**, but browser automation is unreliable in practice — frequently failing and requiring retries; browser testing often requires manual intervention. GitHub Copilot and Amazon Q have no browser automation and require fully manual testing. Windsurf FedRAMP has Playwright but it fails frequently, compounded by the known working-folder bug. **This is a limiting factor for QC/QA workflows.** **Claude Code is the clear leader**: Playwright MCP + Chrome Extension + CLI gives it a 9/10 full dev loop score, three access modes (CLI, VS Code Extension, Mobile), and the deepest automation stack of any tool evaluated.

2. **Script execution is the essential escape hatch for agentic AI.** The ability to write a Python, PowerShell, or Bash script and run it within a single agentic session is the key mechanism for tasks no MCP server covers — connecting to databases, calling proprietary APIs, one-off data transforms, or complex automation chains. Claude Code, Devin, Cursor, and Windsurf Pro all support full script execution autonomously. GitHub Copilot and Amazon Q can generate scripts but execution requires a manual step. Windsurf FedRAMP has severely restricted script execution in its government environment. Skills that combine script execution with AI context (e.g., CLAUDE.md skill docs + MCP tools) multiply this capability into repeatable, team-wide automation.

3. **Claude Code has the strongest plans and skills support of any tool evaluated.** Native task planning via TodoWrite, CLAUDE.md skill docs, MCP tool-calling, and hooks enable fully customized, repeatable AI workflows. No other tool comes close for teams with established AI skill libraries.

4. **FedRAMP compliance eliminates most options.** Only GitHub Copilot (via GitHub Enterprise), Amazon Q Developer (via AWS GovCloud), and Windsurf FedRAMP hold FedRAMP authorization. Of these, GitHub Copilot offers the best capability trade-off. Windsurf FedRAMP is a last resort.

5. **Windsurf FedRAMP has a critical working-folder bug.** The agent intermittently escapes the project root and reads/writes files outside the intended directory — a data integrity and security risk in multi-project environments. This is a known, unresolved issue.

6. **Devin is purpose-built for autonomous task execution, not daily use.** At $500/seat/month it is 10x more expensive than IDE assistants. ROI is only justifiable for well-scoped, high-complexity feature builds.

7. **Cursor is the best IDE-native complement to Claude Code.** It is model-configurable (including Claude backends), cost-effective at $20/month, and ideal for teams who prefer an embedded IDE experience over terminal-first workflows.

8. **Windsurf Pro is a legitimate Tier 2 alternative.** Cascade provides full agentic capability (terminal, multi-file, browser), and it ships with frontier models (Claude Sonnet, GPT-4o). At $15/month it is $5 cheaper than Cursor. Choose Windsurf Pro for an agent-first integrated workflow; choose Cursor for maximum model flexibility and .cursorrules per-repo configuration.

9. **Browser automation via Chrome Extension bypasses federal government integration blockers.** Government networks frequently block external sites and APIs without a GFE (Government Furnished Equipment) browser session. The Claude Code Chrome Extension solves this by operating through an already-authenticated browser — the agent can be authorized for a session using the browser's existing credentials and cookies, allowing it to interact with blocked sites, authorized portals, and GFE-gated APIs that a direct API call or CLI cannot reach. This is a significant differentiator for government-adjacent work and a practical workaround for integration testing in restricted environments. Windsurf Pro and Cursor can open a browser via Playwright but cannot leverage an existing authenticated session the same way.

10. **A cohesive AI ecosystem across all roles delivers more value than a developer-only tool.** Limiting AI tooling to developers leaves architects, PMs, BAs, and QA without AI productivity gains — and creates friction when teams need to collaborate around AI-generated work. Only **Claude Code** serves all roles from a single platform: developers via CLI and VS Code Extension, QA via Playwright automation, architects via MCP/skills design, Automation Engineers via pipeline scripting and E2E browser testing, and PMs/BAs via the Claude.ai desktop app and VS Code Extension (with mobile as a complement). Every other tool is developer-only (Cursor, Windsurf Pro) or developer-primary with partial exceptions (GitHub Copilot via github.com, Devin via Slack). **Selecting a tool that serves the whole organization, not just coders, compounds the productivity investment.**

11. **Amazon Q Developer is only competitive in AWS-centric stacks.** Its model quality trails the field for general-purpose coding but adds meaningful value for CDK, CloudFormation, and Lambda patterns under FedRAMP.

### Recommendations at a Glance

#### By Deployment Environment

| Environment | Recommended Tool | Rationale |
|---|---|---|
| Standard development | **Claude Code** | 9/10 across all criteria; best agentic ecosystem |
| IDE-first — model flexible | **Cursor** | Model-configurable, $20/mo, .cursorrules per repo |
| IDE-first — agent-first | **Windsurf Pro** | Cascade full agentic, frontier models, $15/mo |
| Autonomous task execution | **Devin** (selective) | High cost — pilot before committing |
| FedRAMP — general | **GitHub Copilot** (GHE) | Best capability/compliance balance |
| FedRAMP — AWS stacks | **Amazon Q Developer** | GovCloud authorized, strong for AWS IaC |
| FedRAMP — last resort | **Windsurf FedRAMP** | Only if GHE and Q are not viable |

#### By Role — Who Uses What

| Role | Primary Tool | Why | Secondary / Complement |
|---|---|---|---|
| **Technical Architect** | **Claude Code** | Full dev loop (code → API → browser → fix) is the primary evaluation criterion; MCP/skills design; Chrome Extension bypasses GFE-blocked sites/APIs for gov-adjacent integration testing | Windsurf Pro (agent-first IDE evaluation); GitHub Copilot (FedRAMP strategy) |
| **Principal Developer** | **Claude Code** | Highest model quality, full agentic loop (code → API → browser → fix), script execution | Windsurf Pro (agent-first IDE preference, $15/mo); Cursor (model-flexible IDE); Devin (delegate isolated builds) |
| **Junior Developer** | **Claude Code** (VS Code Ext) or **Windsurf Pro** | Full agentic support from day one — juniors benefit most from AI doing the heavy lifting; VS Code Extension or Cascade provides guided agentic in a familiar IDE | Cursor (model-flexible IDE alternative); GitHub Copilot (lowest friction if GHE is in place) |
| **QC / QA Engineer** | **Claude Code** | Only tool with reliable browser automation (Playwright MCP + Chrome Extension) for agentic test runs | Devin (autonomous regression execution) |
| **Project Manager** | **Claude Code** (desktop app + VS Code Ext) | Claude.ai desktop for planning, doc review, and repo Q&A; VS Code Extension for codebase context; mobile as a complement on the go | Devin via Slack (assign autonomous tasks from phone) |
| **Business Analyst** | **Claude Code** (desktop app + VS Code Ext) | Claude.ai desktop for requirements drafting, doc generation, and codebase Q&A; VS Code Extension for in-repo context; mobile as a complement | GitHub Copilot via github.com (PR review context) |
| **Automation Engineer** | **Claude Code** | Full CLI agentic loop for CI/CD pipeline automation, script execution (Python/Bash/PowerShell), Playwright for E2E testing; Chrome Extension authorizes agent through GFE-gated portals | Devin (autonomous pipeline task delegation); GitHub Copilot (GitHub Actions integration) |

> **Key insight:** Claude Code is the only tool that serves every role — developers via CLI and VS Code Extension, QA via Playwright automation, architects via MCP and skill design, and non-coders (PMs, BAs) via the Claude.ai desktop app and VS Code Extension, with mobile as a complement. A cohesive org-wide AI ecosystem requires a tool that spans roles, not just coders.

---

## Problem Statement

**Current Situation:**
- Development teams require AI-assisted coding tools for accelerated delivery
- Seven candidate platforms exist with materially different capability, reliability, and compliance profiles
- No formal selection criteria established for government/enterprise contexts

**Critical Risks:**
1. **FedRAMP Non-Compliance** — Selecting a tool that cannot operate in government-authorized environments blocks deployment entirely
2. **Unreliable Browser Automation** — Low-reliability tooling degrades AI agent workflows and increases rework
3. **Performance Gaps** — Underperforming AI models slow developer throughput and increase bug introduction risk
4. **Cost Misalignment** — Autonomous-agent tools (Devin) carry per-seat costs 10x+ higher than IDE-assistant tools

**Impact:** Tool selection directly affects developer productivity, compliance posture, automation capability, and budget.

---

## Outcome Expectation

**Primary Goal:** Select an AI coding assistant that delivers high performance, reliability, and browser automation capability while meeting security and compliance requirements.

**Success Metrics:**
- Selected tool scores >= 7/10 across all critical criteria
- FedRAMP authorization met for any government-environment deployments
- Browser automation workflows execute reliably with minimal manual intervention
- Developer adoption >= 80% within 30 days of rollout
- Licensing cost justified by measurable productivity gain

---

## Requirements

### Functional Requirements
1. AI code generation, completion, and explanation (inline and chat)
2. Browser automation support (Playwright or equivalent) for AI agent workflows
3. Terminal/CLI integration for agentic task execution
4. Script execution capability (Python, PowerShell, Bash) for one-off automation and DB/API access without MCP servers
5. Extension ecosystem for IDE and workflow customization
6. Cross-role accessibility — tool must serve developers, architects, PMs, BAs, and QA; not developer-only

### Non-Functional Requirements
1. **Security:** FedRAMP authorization required for government network use
2. **Reliability:** Tool must operate consistently without frequent outages or degraded responses
3. **Performance:** AI model must produce high-quality, accurate code suggestions
4. **Cost:** Licensing must be justifiable against productivity gains
5. **Compliance:** Data handling must meet government data classification requirements

---

## Design Details

### Options Analysis — Full Comparison

| **Criteria** | **Claude Code** | **Devin** | **Cursor** | **Windsurf Pro** | **GitHub Copilot** | **Amazon Q Dev** | **Windsurf FedRAMP** |
|---|---|---|---|---|---|---|---|
| **⭐ Full Dev Loop** *(primary)* | ✅ 9/10 — Code → run API → open browser → inspect UI → fix, fully agentic | ✅ 8/10 — Autonomous end-to-end; harder to steer mid-loop | ⚠️ 4/10 — Code + terminal tests solid; CAN open browser via Playwright but unreliable, requires retries | ⚠️ 5/10 — Cascade + Playwright CAN open browser; unreliable, requires retries; code + terminal steps solid | ❌ 2/10 — No browser automation; testing is manual | ❌ 2/10 — No browser automation | ❌ 2/10 — Playwright available; frequently fails + folder bug contaminates environment |
| **⭐ Agentic CLI/Terminal** *(primary)* | ✅ Full (CLI + MCP) | ✅ Fully Autonomous | ✅ Composer/Agent | ✅ Full (Cascade agent) | ⚠️ Limited | ⚠️ Limited | ❌ Minimal |
| **⭐ Plans Support** *(primary)* | ✅ Native (TodoWrite, multi-step plans) | ✅ Native (autonomous planning) | ⚠️ Partial (no persistent plan) | ⚠️ Partial (basic task flow) | ⚠️ Partial (Copilot Workspace; limited) | ❌ Minimal | ❌ None |
| **⭐ Skills / Custom Workflows** *(primary)* | ✅ Full (CLAUDE.md, MCP tools, skill docs, hooks) | ⚠️ Limited (task instructions only) | ⚠️ Partial (.cursorrules per repo) | ⚠️ Partial (workspace rules; limited) | ⚠️ Partial (custom instructions only) | ❌ Minimal | ❌ None (restricted) |
| **⭐ Script Execution** *(primary)* | ✅ Full — writes + runs Python/Bash/PowerShell in session; primary escape hatch for DB, APIs, one-off automation | ✅ Full — cloud shell runs any script autonomously | ✅ Full — Composer writes scripts, terminal runs them | ✅ Full — Cascade writes + runs scripts via terminal | ⚠️ Partial — generates scripts; execution requires manual step | ⚠️ Partial — generates scripts; execution requires manual step | ❌ Minimal — restricted environment; unreliable execution |
| **⭐ Team Ecosystem Breadth** *(primary)* | ✅ Full org — Devs (CLI/VS Code), Architects (MCP/skills design), PMs/BAs (desktop app + VS Code Ext, mobile as complement), QA/Automation (Playwright) — one platform for all roles | ⚠️ Dev + PM — Devs code, PMs assign via Slack; BAs/QA have no interface | ❌ Dev only — no interface for PMs, BAs, or non-coders | ❌ Dev only — no interface for PMs, BAs, or non-coders | ⚠️ Dev + limited PM/BA — github.com gives PMs/BAs PR visibility; no coding alternative | ❌ Dev/AWS only — no org-wide value | ❌ Dev only (restricted) — narrowest reach of all options |
| **Performance** | 9/10 | 8/10 | 8/10 | 7/10 | 7/10 | 6/10 | 3/10 |
| **Reliability** | 9/10 | 7/10 | 7/10 | 6/10 | 9/10 | 8/10 | 3/10 |
| **Browser Automation** | 9/10 | 9/10 | 4/10 | 6/10 | 3/10 | 2/10 | 3/10 |
| **Model Quality** | ✅ Claude 4.x | ✅ Proprietary + Claude | ✅ Configurable (Claude/GPT) | ✅ Frontier models (Claude, GPT-4o) | ⚠️ GPT-4o only | ⚠️ Amazon models | ❌ Degraded |
| **Mobile Access** | ✅ iOS/Android (Claude app + GitHub repos; CLI via SSH) | ✅ iOS/Android (Slack mobile + web UI task assignment) | ❌ Desktop only | ❌ Desktop only | ⚠️ Limited (github.com mobile; no code editing) | ❌ Desktop/IDE only | ❌ Desktop only |
| **Extension Ecosystem** | ✅ Rich (MCP) | ⚠️ Proprietary | ✅ Moderate | ✅ Moderate | ✅ Rich (GH ecosystem) | ⚠️ AWS-centric | ❌ Restricted |
| **FedRAMP Authorized** | ⚠️ Roadmap | ❌ No | ❌ No | ❌ No | ✅ Yes (GHE) | ✅ Yes (GovCloud) | ✅ Yes |
| **Offline Capability** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ⚠️ Limited |
| **Pricing Model** | API usage-based | Per seat/month | Per seat/month | Per seat/month | Per seat/month | Per seat/month | Per seat/month |
| **Individual / Team** | $3/M (Sonnet) – $15/M (Opus) tokens | $500/seat/mo | $20/seat/mo | $15/seat/mo | $19/seat/mo (Ind.) / $39/seat/mo (Ent.) | $19/seat/mo (free tier avail.) | Custom (Enterprise+ via Palantir FedStart) |
| **Est. Cost / Dev / Mo** | ~$50–200 (moderate use) | $500 (fixed) | $20 | $15 | $19–39 | $19 (or free) | ~$60–100+/mo (custom quote required) |
| **Overall Score** | **9/10** | **8/10** | **7.5/10** | **7.5/10** | **6.5/10** | **5.5/10** | **3/10** |

### Full Dev Loop — Tool Coverage

The ability to **write code → test an API → open a browser → test the UI → fix any issues** in a single uninterrupted agentic session is the highest-value capability evaluated. Only two tools complete this loop without manual handoffs.

```mermaid
graph LR
    subgraph LOOP["Full Dev Loop"]
        S1["1. Write Code\nAPI + UI"]
        S2["2. Run API Tests\nTerminal / CLI"]
        S3["3. Open Browser\nNavigate to UI"]
        S4["4. Inspect UI\nVisual + functional"]
        S5["5. Identify Issues\nErrors / layout bugs"]
        S6["6. Fix Code\nIterate automatically"]
        S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S1
    end

    subgraph FULL["Full Loop — Autonomous"]
        CC2["Claude Code\nCLI + Playwright MCP\n+ Chrome Extension\n9/10"]
        DV2["Devin\nBuilt-in browser\n+ autonomous shell\n8/10"]
    end

    subgraph PARTIAL["Partial Loop — Browser Unreliable / Code + CLI Only"]
        WP2["Windsurf Pro\nCascade + Playwright\nBrowser CAN open; unreliable\n5/10"]
        CU2["Cursor\nComposer + Terminal\nBrowser CAN open; unreliable\n4/10"]
    end

    subgraph NONE["No Reliable Loop — Manual Testing Required"]
        GC2["GitHub Copilot\nNo browser automation\n2/10"]
        AQ2["Amazon Q Dev\nNo browser automation\n2/10"]
        WF2["Windsurf FedRAMP\nPlaywright available; frequently fails\n+ folder bug\n2/10"]
    end

    style CC2 fill:#2e7d32,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DV2 fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WP2 fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CU2 fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GC2 fill:#b71c1c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AQ2 fill:#b71c1c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WF2 fill:#b71c1c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style S1 fill:#0d47a1,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style S2 fill:#0d47a1,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style S3 fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style S4 fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style S5 fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style S6 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

**Why this matters:** Without a complete loop, developers must manually switch to a browser, identify problems, and context-switch back to the editor. Every handoff breaks the AI's context, increases error rate, and eliminates the compound productivity gain of continuous agentic iteration.

---

### Alternative 1: Claude Code Ecosystem *(Recommended)*

```mermaid
graph TD
    subgraph "Access Methods"
        MOB["Mobile — iOS / Android\nClaude App + GitHub repos\nor CLI via SSH terminal app"]
        EXT["VS Code Extension\nIDE-embedded AI\nInline chat + agent mode"]
        CLI["Claude Code CLI\nTerminal / SSH\nFull agentic loop"]
    end

    subgraph "AI Backend"
        API["Anthropic API\n(Claude Sonnet / Opus 4.x)"]
    end

    subgraph "Automation Layer"
        MCP["MCP Server Ecosystem\nFiles · Git · Slack · Databases"]
        PW["Playwright MCP\n(Browser Automation)"]
        ChrExt["Chrome Extension\n(Browser Automation)"]
    end

    MOB -->|"Code review\nRepo Q&A"| API
    EXT -->|"Inline AI\nAgent edits"| API
    CLI -->|"Agentic tasks\nTerminal commands"| API
    CLI --> MCP
    MCP --> PW
    EXT --> ChrExt
    ChrExt --> PW

    style MOB fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style EXT fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CLI fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style API fill:#2e7d32,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style MCP fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PW fill:#0d47a1,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style ChrExt fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

**Key Points:**
- Three access modes: CLI (traditional), VS Code Extension (IDE-embedded), and Mobile (Claude app on iOS/Android)
- **Only tool (with Devin) that completes the full dev loop:** write API → run tests in terminal → open browser via Playwright MCP or Chrome Extension → inspect UI → identify errors → fix code → repeat, all without leaving the agentic session
- Mobile access via Claude.ai app: review GitHub repos, discuss code, get AI-assisted answers anywhere
- CLI via SSH from mobile terminal apps (e.g., Termius) enables full agentic capability from a phone
- VS Code Extension provides inline completions and agent mode without leaving the IDE
- Powered by Claude Sonnet 4.6 / Opus 4.6 — top-tier code generation quality

**Pros:**
- ✅ Full dev loop: 9/10 — only tool that writes, tests, browses, and fixes in one unbroken session
- ✅ Performance: 9/10 — best-in-class code generation
- ✅ Reliability: 9/10 — stable API with high uptime SLAs
- ✅ Browser automation: 9/10 — Playwright MCP + Chrome extension
- ✅ Full CLI/terminal agentic execution (claude-code)
- ✅ Richest MCP extension ecosystem of any tool evaluated
- ✅ Active model improvement cadence (Claude 4.x family)

**Cons:**
- ❌ Not FedRAMP authorized (GovCloud roadmap, not yet available)
- ❌ API cost scales with usage — requires usage governance
- ❌ Cannot be used on classified/IL4+ networks today

**Best For:** Standard development environments, enterprise AI workflows, high-throughput agentic automation.

---

### Alternative 2: Devin (Cognition AI)

```mermaid
graph TD
    subgraph "Access Methods"
        MOBD["Mobile — iOS / Android\nSlack App\n(task assignment from phone)"]
        WEBD["Web Browser\ndevin.ai Dashboard\n(monitoring + assignment)"]
    end

    subgraph "Cognition Cloud — Autonomous Execution"
        DV["Devin Agent"]
        BR["Built-in Browser"]
        SH["Shell / Terminal"]
        FS["File System"]
    end

    subgraph "AI Backend"
        DVAPI["Cognition AI Models\n(+ Claude/GPT integration)"]
    end

    MOBD -->|"Assign task\nvia Slack"| DV
    WEBD -->|"Assign task\nMonitor progress"| DV
    DV --> DVAPI
    DV --> BR
    DV --> SH
    DV --> FS

    style MOBD fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WEBD fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style DV fill:#2e7d32,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DVAPI fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style BR fill:#0d47a1,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style SH fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style FS fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

**Key Points:**
- Fully autonomous AI software engineer — operates independently in a cloud environment
- Assigned tasks via Slack or web UI; executes end-to-end without developer intervention
- Has its own browser, shell, and file system — highest autonomy of any tool evaluated
- Best suited for well-scoped, isolated tasks; can go off-rails on ambiguous requirements

**Pros:**
- ✅ Performance: 8/10 — handles complex multi-step coding tasks autonomously
- ✅ Browser automation: 9/10 — built-in browser, no external Playwright setup needed
- ✅ Fully autonomous — frees developers from repetitive implementation work
- ✅ Native Slack integration for task assignment

**Cons:**
- ❌ Cost: $$$$ — ~$500/seat/month, 10x+ higher than IDE-assistant tools
- ❌ Not FedRAMP authorized
- ⚠️ Reliability: 7/10 — can fail on ambiguous or under-specified tasks
- ⚠️ Proprietary cloud environment — limited auditability and control
- ❌ Not suitable for sensitive code or air-gapped environments
- ⚠️ Requires careful task scoping; autonomous failures can compound

**Best For:** High-value, well-scoped autonomous tasks (e.g., "build this feature end-to-end") where developer time is more expensive than tooling cost. Not a daily-driver replacement.

---

### Alternative 3: Cursor

```mermaid
graph TD
    subgraph "Access Methods"
        DESKC["Desktop Only\nWindows / Mac / Linux\nNo mobile support"]
    end

    subgraph "Cursor IDE"
        CUR["Cursor (VS Code fork)\nInline AI + Chat"]
        COMP["Composer / Agent Mode\nMulti-file edits"]
        TERM["Integrated Terminal"]
    end

    subgraph "AI Backend — Configurable"
        CAPI["Claude Sonnet/Opus\nor GPT-4o\nor Gemini"]
    end

    DESKC --> CUR
    CUR --> COMP
    CUR --> TERM
    COMP -->|"Choose model\nper task"| CAPI

    style DESKC fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CUR fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style COMP fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CAPI fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style TERM fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

**Key Points:**
- VS Code fork with deep AI integration at the IDE level
- Model-agnostic: configurable to use Claude, GPT-4o, or Gemini backends
- Composer/Agent mode enables multi-file agentic edits with terminal access
- Strong inline autocomplete + chat; lacks native browser automation layer

**Pros:**
- ✅ Performance: 8/10 — excellent when configured with Claude backend
- ✅ Model flexibility — choose best model per task
- ✅ Strong Composer agent for multi-file refactors
- ✅ Predictable subscription cost (~$20/month)
- ✅ Familiar VS Code experience with AI deeply embedded

**Cons:**
- ❌ Full dev loop: 4/10 — Composer can write code and run terminal tests, but cannot open a browser, visually inspect the UI, or interact with web pages in the agentic loop; browser testing requires manual handoff
- ❌ Not FedRAMP authorized
- ⚠️ Reliability: 7/10 — smaller infra than Microsoft or Anthropic
- ⚠️ Agent mode less mature than Claude Code CLI for complex terminal workflows
- ❌ No MCP ecosystem equivalent

**Best For:** Teams wanting best-in-class IDE experience with model flexibility and strong multi-file agent edits. Excellent Claude Code complement for developers who prefer an IDE over CLI.

---

### Alternative 4: Windsurf Pro

```mermaid
graph TD
    subgraph "Access Methods"
        DESKW["Desktop Only\nWindows / Mac / Linux\nNo mobile support"]
    end

    subgraph "Windsurf IDE"
        WS["Windsurf (VS Code fork)\nInline AI + Chat"]
        PW2["Playwright Extension\n(Browser Automation)"]
    end

    subgraph "AI Backend"
        WSAPI["Windsurf AI Backend\n(GPT-4o / Claude mix — variable)"]
    end

    DESKW --> WS
    WS --> WSAPI
    WS --> PW2

    style DESKW fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WS fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WSAPI fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PW2 fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

**Key Points:**
- IDE-first experience (forked from VS Code) with Cascade — a purpose-built full agentic system
- Cascade handles multi-file edits, terminal command execution, and web browsing autonomously
- Ships with frontier models: Claude Sonnet, GPT-4o — model quality is not a limitation
- Priced at $15/month — $5 cheaper than Cursor with comparable agentic capability
- Primary differentiator vs. Cursor: Windsurf is agent-first (Cascade); Cursor is model-flexible (Composer)

**Pros:**
- ✅ Performance: 7/10 — strong, backed by frontier models
- ✅ Agentic: Full — Cascade agent runs terminal, multi-file edits, and browser tasks
- ✅ Model quality: Frontier (Claude Sonnet, GPT-4o) — not variable or degraded
- ✅ Familiar VS Code experience with deep agent integration
- ✅ $15/month — competitive price, $5 less than Cursor
- ✅ Playwright integration for browser automation

**Cons:**
- ⚠️ Full dev loop: 5/10 — Cascade CAN open a browser via Playwright and run tests, but browser automation is unreliable in practice — frequently fails and requires retries; code + terminal testing steps are solid, but browser inspection is not seamless; limiting for QC/QA workflows
- ❌ Not FedRAMP authorized
- ⚠️ No MCP ecosystem — can't extend with custom tool servers
- ⚠️ No mobile access — desktop only
- ⚠️ Less model flexibility than Cursor — model selection more constrained

**Best For:** Developers who want a strong agent-first IDE experience at a lower price point than Cursor. A legitimate alternative to Cursor; choose based on whether you prefer Cascade's integrated agentic flow (Windsurf) or maximum model flexibility (Cursor).

---

### Alternative 5: GitHub Copilot

```mermaid
graph TD
    subgraph "Access Methods"
        GHDESK["Desktop IDE\nVS Code / JetBrains\nVisual Studio / Neovim"]
        GHWEB["github.com\nCopilot Chat in browser\n(PR review + code Q&A)"]
        GHMOB["GitHub Mobile App\niOS / Android\nPR review — limited Copilot chat"]
    end

    subgraph "GitHub / Microsoft Backend"
        GHAPI["GPT-4o\n(Azure OpenAI)"]
        GHE["GitHub Enterprise\n(FedRAMP High)"]
        CWS["Copilot Workspace\n(Agent Mode)"]
    end

    GHDESK -->|"Inline completions\nChat + agent"| GHAPI
    GHWEB -->|"Web-based chat\nCode review"| GHAPI
    GHMOB -->|"PR reviews\nLimited chat"| GHAPI
    GHDESK --> CWS
    CWS --> GHE

    style GHDESK fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GHWEB fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GHMOB fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GHAPI fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GHE fill:#2e7d32,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style CWS fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

**Key Points:**
- Most widely deployed enterprise AI coding tool globally
- FedRAMP High authorization available via GitHub Enterprise + Azure GovCloud
- Deeply integrated into GitHub platform (PRs, issues, Actions)
- Strong inline autocomplete; agent/autonomous mode (Copilot Workspace) still maturing

**Pros:**
- ✅ FedRAMP authorized via GitHub Enterprise (GHE) — viable government option
- ✅ Reliability: 9/10 — Microsoft Azure infrastructure, enterprise SLAs
- ✅ Broadest IDE support (VS Code, JetBrains, Visual Studio, Neovim)
- ✅ GitHub platform integration (PR reviews, issue resolution, Actions)
- ✅ Familiar to most developers — lowest adoption friction
- ✅ Predictable per-seat pricing ($19–39/month)

**Cons:**
- ⚠️ Performance: 7/10 — GPT-4o based; strong but not best-in-class for complex tasks
- ❌ Browser automation: 3/10 — no native browser automation capability
- ⚠️ Agentic CLI: 5/10 — Copilot Workspace improving but not production-grade yet
- ⚠️ FedRAMP path requires full GHE licensing — adds cost and procurement complexity
- ⚠️ Model locked to GPT-4o — no Claude option

**Best For:** Organizations already on GitHub Enterprise seeking a compliant, low-friction AI coding tool. Best FedRAMP option when browser automation is not a requirement.

---

### Alternative 6: Amazon Q Developer

```mermaid
graph TD
    subgraph "Access Methods"
        AQDESK["Desktop IDE\nVS Code / JetBrains\n(primary experience)"]
        AQWEB["AWS Console — Web\nLimited Q chat\n(no mobile app)"]
    end

    subgraph "AWS Backend"
        AQAPI["Amazon AI Models\n(Amazon Nova / Bedrock)"]
        AQA["Q Developer Agent\n(/dev command)"]
        GC["AWS GovCloud\n(FedRAMP High)"]
    end

    AQDESK -->|"Inline completions\nChat + /dev agent"| AQAPI
    AQWEB -->|"Limited Q chat\nin browser"| AQAPI
    AQDESK --> AQA
    AQA --> GC

    style AQDESK fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AQWEB fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AQAPI fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AQA fill:#e65100,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GC fill:#2e7d32,stroke:#ffffff,stroke-width:3px,color:#ffffff
```

**Key Points:**
- FedRAMP High authorized via AWS GovCloud — strongest compliance posture of all options
- Optimized for AWS service integration (CDK, CloudFormation, Lambda, S3)
- `/dev` agent mode handles multi-file feature implementation
- Model quality trails Claude and GPT-4o; best in class for AWS-specific patterns

**Pros:**
- ✅ FedRAMP High via AWS GovCloud — strongest compliance posture evaluated
- ✅ Reliability: 8/10 — AWS infrastructure
- ✅ Optimized for AWS-centric codebases and IaC
- ✅ Free tier available; paid tier ~$19/month
- ✅ Broad IDE support (VS Code, JetBrains, CLI)

**Cons:**
- ⚠️ Performance: 6/10 — Amazon models lag Claude/GPT-4o on general coding tasks
- ❌ Browser automation: 2/10 — essentially none
- ⚠️ Agentic CLI: 5/10 — `/dev` agent improving but limited vs. Claude Code
- ❌ Weak value outside AWS ecosystem; poor for Salesforce, .NET, or non-AWS stacks
- ⚠️ Extension ecosystem AWS-centric — limited MCP/third-party integrations

**Best For:** AWS-heavy shops requiring FedRAMP compliance where GitHub Copilot is not already in use. Poor fit for non-AWS stacks.

---

### Alternative 7: Windsurf FedRAMP *(Compliance-Only)*

```mermaid
graph TD
    subgraph "Access Methods"
        DESKFR["Desktop Only\nGovernment Network\nNo mobile support"]
    end

    subgraph "Government Network — FedRAMP Boundary"
        WS_FR["Windsurf FedRAMP IDE"]
        BUG["Known Bug: File Access\nAgent escapes working folder\nreads/writes outside project root"]
        PW3["Playwright\n(Unreliable)"]
    end

    subgraph "Restricted AI Backend"
        FR_API["Windsurf Gov AI Backend\n(Older/degraded models)"]
    end

    DESKFR --> WS_FR
    WS_FR --> FR_API
    WS_FR -.->|"limited + buggy"| PW3
    WS_FR -.->|"unintended\nfile access"| BUG

    style DESKFR fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WS_FR fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style FR_API fill:#b71c1c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PW3 fill:#b71c1c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style BUG fill:#b71c1c,stroke:#ffffff,stroke-width:3px,color:#ffffff
```

**Key Points:**
- FedRAMP authorized — required for government network deployments where GHE/AWS Q are not options
- AI model performance significantly degraded versus commercial counterparts
- Browser automation (Playwright) available but unreliable — frequently fails, requires retries
- **Known bug:** Agent does not reliably respect the working folder boundary — reads and writes files outside the project root, causing unintended modifications to other directories and posing a data integrity risk
- **Pricing:** Custom Enterprise via Palantir FedStart — expect ~$60–100+/user/month; requires government procurement contract and contract amendment to expand credits
- Weakest overall option evaluated; included for completeness

**Pros:**
- ✅ FedRAMP authorized — valid for IL2/IL4 environments
- ✅ Meets government data residency and compliance requirements

**Cons:**
- ❌ Performance: 3/10 — degraded model quality
- ❌ Reliability: 3/10 — frequent instability
- ❌ Browser automation: 3/10 — Playwright available but unreliable
- ❌ **Working-folder bug:** Agent escapes project root and reads/writes files in parent or sibling directories — unresolved, poses data integrity and security risk in multi-project workspaces
- ❌ Plans support: None — no structured task planning capability
- ❌ Skills support: None — restricted environment blocks custom workflow tooling
- ❌ Mobile access: None — desktop/government network only
- ❌ Restricted extension ecosystem
- ❌ Limited agentic/CLI capability
- ❌ Older/smaller models — lowest code quality of all options evaluated

**Best For:** Government environments where GHE and Amazon Q are not viable and FedRAMP is a hard requirement. Last resort only.

---

## Scoring Summary

```mermaid
graph TD
    subgraph T1["Tier 1 — Recommended"]
        CC["Claude Code — 9/10\nStandard environments\nBest agentic ecosystem"]
    end

    subgraph T2["Tier 2 — Strong Alternatives"]
        DV["Devin — 8/10\nAutonomous tasks\nHigh cost — pilot first"]
        CU["Cursor — 7.5/10\nIDE-first, model-flexible\nComposer agent"]
        WP["Windsurf Pro — 7.5/10\nIDE-first, agent-first\nCascade agent"]
    end

    subgraph T3["Tier 3 — Situational"]
        GC["GitHub Copilot — 6.5/10\nFedRAMP via GHE\nBest compliant option"]
    end

    subgraph T4["Tier 4 — Compliance / Niche"]
        AQ["Amazon Q Dev — 5.5/10\nFedRAMP via GovCloud\nAWS stacks only"]
        WF["Windsurf FedRAMP — 3/10\nFedRAMP last resort\nKnown folder bug"]
    end

    T1 --> T2
    T2 --> T3
    T3 --> T4

    style CC fill:#2e7d32,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DV fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CU fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WP fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style GC fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AQ fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style WF fill:#b71c1c,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

---

## Persona Guide

### Persona Profiles

| Persona | Primary Needs | Key Constraints |
|---|---|---|
| **Technical Architect** | Tool evaluation, compliance strategy, workflow design, skills/MCP setup | Must assess FedRAMP posture; sets standards for the team |
| **Principal Developer** | Full agentic capability, complex multi-file tasks, mentoring via shared workflows | Needs highest model quality; drives skill/CLAUDE.md authoring |
| **Junior Developer** | Inline completions, guided suggestions, low-friction IDE experience | Needs safety guardrails; benefits from IDE-native over CLI-first |
| **QC / QA Engineer** | Browser automation, test generation, regression execution | Browser automation reliability is critical; agentic loop for test runners |
| **Project Manager** | Mobile task assignment, progress visibility, planning support | Not writing code; needs lightweight access — mobile + dashboards |
| **Business Analyst** | Documentation generation, requirements analysis, codebase Q&A | Minimal coding; needs natural language interface to repos and docs |
| **Automation Engineer** | CI/CD pipeline automation, E2E test automation, deployment orchestration, infrastructure scripting | Needs reliable script execution, agentic CLI, Playwright for UI test automation in pipelines; government network integration workarounds via browser agent |

---

### Persona × Tool Matrix

| **Persona** | **Claude Code** | **Devin** | **Cursor** | **Windsurf Pro** | **GitHub Copilot** | **Amazon Q** | **Windsurf FedRAMP** |
|---|---|---|---|---|---|---|---|
| **Technical Architect** | ✅ Primary — full capability + skills/MCP design | ⚠️ Evaluate for autonomous task delegation | ✅ Complement — model-flexible IDE | ✅ Complement — agent-first IDE (Cascade) | ✅ FedRAMP strategy + GHE compliance | ⚠️ FedRAMP + AWS stacks only | ⚠️ FedRAMP only — document bug risk |
| **Principal Developer** | ✅ Primary — CLI + MCP + full agentic loop | ⚠️ Delegate isolated high-complexity builds | ✅ Complement — model-flexible IDE preference | ✅ Complement — Cascade agent-first preference | ⚠️ FedRAMP environments only | ❌ AWS-only value | ⚠️ FedRAMP only — last resort |
| **Junior Developer** | ✅ Primary — VS Code Extension gives full agentic in a familiar IDE; juniors benefit most from AI doing the heavy lifting | ❌ Too autonomous — masks learning, no feedback loop | ✅ Strong — model-flexible IDE, Composer agentic; good alternative | ✅ Primary — Cascade agentic in IDE; guided, fast, $15/mo; excellent entry point | ✅ Complement — lowest adoption friction if GHE in place | ❌ Weak general-purpose model | ❌ Avoid — bugs + degraded model impedes learning |
| **QC / QA Engineer** | ✅ Primary — best browser automation (Playwright MCP + Chrome ext); fastest, most reliable agentic test loop | ✅ Delegate autonomous test execution | ⚠️ Limited automation; use for test code authoring only | ⚠️ Windsurf Pro Cascade + Playwright WILL work for browser testing but slower, less reliable, and requires retries — acceptable fallback, not recommended primary | ❌ No browser automation | ❌ No browser automation | ❌ Unreliable automation + folder bug risk |
| **Project Manager** | ✅ Desktop app + VS Code Ext — Claude.ai desktop for planning + doc review; VS Code Ext for repo context; mobile as complement | ✅ Slack desktop — assign tasks, monitor progress; mobile as complement | ❌ Developer tool only | ❌ Developer tool only | ⚠️ github.com — PR visibility; limited PM utility | ❌ No PM value | ❌ No PM value |
| **Business Analyst** | ✅ Desktop app + VS Code Ext — Claude.ai desktop for doc gen, requirements drafting, codebase Q&A; mobile as complement | ❌ Too autonomous; no BA-facing interface | ⚠️ Code context chat; no BA-specific features | ⚠️ Code context chat via Cascade; no BA-specific features | ⚠️ github.com chat for codebase Q&A | ❌ No BA value | ❌ No BA value |
| **Automation Engineer** | ✅ Primary — full CLI agentic loop for pipeline automation + script execution; Playwright MCP + Chrome Extension for E2E and gov-blocked site access via authorized browser session | ✅ Delegate autonomous pipeline tasks and deployment runs | ⚠️ Good for pipeline script authoring; limited E2E browser automation | ⚠️ Cascade handles pipeline scripts well; browser automation unreliable for CI test loops | ✅ Strong — GitHub Actions integration, CI/CD-native; good complement | ⚠️ AWS pipeline automation only | ❌ Restricted environment blocks most automation tooling |

**Legend:** ✅ Recommended · ⚠️ Situational / With Caveats · ❌ Not Recommended

---

### Persona Workflow Diagrams

#### When to Use Each Tool by Role

```mermaid
graph TD
    subgraph "Technical Architect"
        TA1["Claude Code\nSkills + MCP design\nCompliance assessment"]
        TA2["GitHub Copilot\nFedRAMP strategy"]
    end

    subgraph "Principal Developer"
        PD1["Claude Code CLI\nFull agentic loop"]
        PD2["Cursor\nIDE-native edits"]
        PD3["Devin\nDelegate isolated builds"]
    end

    subgraph "Junior Developer"
        JD1["Claude Code\nVS Code Extension\nFull agentic — guided in IDE"]
        JD2["Windsurf Pro\nCascade agentic — IDE\nAffordable + full agentic"]
        JD3["Cursor\nAlternative — model-flexible\nComposer agentic"]
    end

    subgraph "QC / QA Engineer"
        QC1["Claude Code\nPlaywright MCP\nChrome Extension"]
        QC2["Devin\nAutonomous test runs"]
    end

    subgraph "Project Manager"
        PM1["Claude Code\nDesktop app + VS Code Ext\nPlanning + doc review + repo Q&A"]
        PM2["Devin\nSlack desktop + mobile\nAssign + monitor autonomous tasks"]
    end

    subgraph "Business Analyst"
        BA1["Claude Code\nDesktop app + VS Code Ext\nDoc gen + requirements + codebase Q&A"]
        BA2["GitHub Copilot\ngithub.com chat\nPR review context"]
    end

    subgraph "Automation Engineer"
        AE1["Claude Code CLI\nPlaywright MCP + Chrome Ext\nCI/CD automation + E2E testing"]
        AE2["Claude Code\nChrome Extension\nBypasses GFE-blocked portals\nvia authorized browser session"]
        AE3["GitHub Copilot\nGitHub Actions integration\nCI pipeline authoring"]
    end

    style TA1 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style TA2 fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PD1 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PD2 fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PD3 fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style JD1 fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style JD2 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style JD3 fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style QC1 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style QC2 fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PM1 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style PM2 fill:#00695c,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style BA1 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style BA2 fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AE1 fill:#2e7d32,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AE2 fill:#6a1b9a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style AE3 fill:#1565c0,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

---

### Per-Persona Recommendations

#### Technical Architect
- **Primary:** Claude Code — the full dev loop (code → API → browser → fix) is the primary evaluation criterion for tool selection; must be assessed hands-on, not just on paper
- **Complement:** Windsurf Pro — evaluate as agent-first IDE alternative for developer teams; Cascade provides full agentic at $15/mo; understand its browser automation limitations (reliable for code + terminal, unreliable for visual inspection loops) before recommending to QA or Automation teams
- **Complement:** GitHub Copilot (GHE) — preferred FedRAMP-compliant option; assess GHE licensing status early
- **Key capability:** Chrome Extension enables the agent to operate through an existing authenticated browser session — critical for government-adjacent environments where sites and APIs are blocked without a GFE; direct API calls and CLI cannot bypass these controls, but the browser plugin can authorize the agent for a session
- **FedRAMP:** GitHub Copilot (GHE) as preferred compliant option; Amazon Q if AWS-centric; Windsurf FedRAMP as last resort only
- **Action:** Author team CLAUDE.md and skill docs; define MCP server standards; assess Windsurf FedRAMP folder bug risk before deployment; document Chrome Extension session-auth workflow for gov integration testing

#### Principal Developer
- **Primary:** Claude Code CLI — highest model quality, full agentic loop (code → API → browser → fix), script execution, terminal authority
- **Complement:** Windsurf Pro — agent-first IDE for developers who prefer staying in an IDE; Cascade provides full agentic including script execution at $15/mo; a strong peer to Cursor, not a downgrade
- **Complement:** Cursor — model-flexible IDE (Claude/GPT/Gemini backends); best when per-repo .cursorrules configuration or maximum model flexibility is required
- **Selective:** Devin for well-scoped autonomous feature builds (validate ROI at $500/seat)
- **Action:** Co-author team skill docs; establish CLAUDE.md patterns; mentor junior devs on VS Code Extension or Windsurf Pro entry path

#### Junior Developer
- **Primary:** Claude Code VS Code Extension or Windsurf Pro — full agentic support from day one; juniors benefit the most from AI doing the heavy lifting; VS Code Extension and Cascade both provide guided agentic inside a familiar IDE without needing CLI fluency
- **Alternative:** Cursor — model-flexible Composer agentic; good if team prefers maximum model choice or .cursorrules per-repo configuration
- **Complement:** GitHub Copilot — lowest adoption friction if GHE is already in place
- **Avoid:** Claude Code raw CLI until comfortable with agentic patterns; Windsurf FedRAMP entirely (bugs + degraded model impedes learning)

#### QC / QA Engineer
- **Primary:** Claude Code — only tool with a complete, reliable browser automation stack (Playwright MCP + Chrome Extension); fastest agentic test loop; writes tests, runs them, opens the browser, inspects the UI, and fixes issues in one session
- **Fallback:** Windsurf Pro — Cascade + Playwright WILL open a browser and execute tests, but it is slower, less reliable, and frequently requires retries; acceptable if Claude Code is unavailable, but expect friction and manual intervention for complex UI flows
- **Selective:** Devin for autonomous regression runs on well-defined, repeatable test suites
- **Avoid:** Cursor (browser automation unreliable, no dedicated test loop), GitHub Copilot, Amazon Q, Windsurf FedRAMP — all have weak or no browser automation

#### Project Manager
- **Primary:** Claude Code desktop app (Claude.ai) + VS Code Extension — desktop is the main working surface for planning sessions, doc review, delivery status Q&A, and repo context; VS Code Extension for in-codebase discussions without requiring CLI knowledge
- **Complement:** Mobile (Claude app on iOS/Android) — on-the-go access to continue desktop sessions, quick repo questions, or review AI-generated summaries between meetings
- **Selective:** Devin via Slack — assign autonomous coding tasks and monitor completion from Slack desktop or mobile
- **Note:** PMs work primarily on desktop; mobile is a complement, not the primary interface

#### Automation Engineer
- **Primary:** Claude Code CLI — full agentic loop for CI/CD pipeline automation; writes and runs Python/Bash/PowerShell scripts for deployment orchestration, test execution, and infrastructure tasks; Playwright MCP for E2E browser test automation integrated into pipeline runs
- **Key capability:** Chrome Extension authorizes the Claude Code agent through an existing GFE browser session — enabling integration testing against government portals, blocked APIs, and authorized sites that would reject direct CLI or API calls; this is a practical workaround for federal integration blockers without needing network-level access changes
- **Complement:** GitHub Copilot — strong for GitHub Actions workflow authoring and CI pipeline code; familiar to DevOps teams already on GHE
- **Selective:** Devin for autonomous deployment task delegation and pipeline health monitoring
- **Avoid:** Windsurf FedRAMP (restricted environment blocks most automation tooling); GitHub Copilot or Amazon Q alone (no reliable browser automation for E2E tests)

#### Business Analyst
- **Primary:** Claude Code desktop app (Claude.ai) + VS Code Extension — desktop is the primary surface for requirements drafting, documentation generation, codebase Q&A, and stakeholder-facing doc creation; VS Code Extension for in-repo context (understanding code without writing it)
- **Complement:** Mobile (Claude app on iOS/Android) — continue desktop sessions, capture quick requirements notes, review AI-drafted content on the go
- **Complement:** GitHub Copilot via github.com — PR review context and issue summarization directly in the browser
- **Note:** BAs benefit most from Claude's conversational and writing strengths; no CLI or coding required

---

### For Developers
- ✅ Claude Code: Maximum productivity — best model, full agentic loop (code → API → browser → fix), MCP ecosystem, script execution
- ✅ Devin: Maximum autonomy — hands-off execution; high cost justified for the right tasks
- ✅ Windsurf Pro: Strong Tier 2 — Cascade agent-first IDE, frontier models, full script execution, $15/mo; best for developers who prefer IDE over CLI; peer to Cursor not inferior
- ✅ Cursor: Best IDE for model flexibility — Claude/GPT/Gemini backends, .cursorrules per repo, $20/mo; complement to both Claude Code and Windsurf Pro
- ⚠️ GitHub Copilot: Good inline completions; lowest adoption friction; weak agentic automation; best for FedRAMP or GHE-native teams
- ⚠️ Amazon Q: Strong only on AWS-centric code; limited general-purpose value
- ❌ Windsurf FedRAMP: Productivity loss; use only when required by compliance

### For Engineering Management
- ✅ Claude Code: Highest ROI in standard environments
- ⚠️ Devin: Very high cost — ROI only for well-scoped autonomous tasks
- ✅ Cursor: Strong ROI, model-flexible, $20/mo — complements Claude Code
- ✅ Windsurf Pro: Strong ROI, agent-first Cascade, $15/mo — legitimate peer to Cursor
- ✅ GitHub Copilot: Best enterprise cost/compliance balance (if GHE in place)
- ⚠️ Amazon Q: Good ROI for AWS shops only
- ⚠️ Windsurf FedRAMP: Compliance necessity; accept productivity cost

### For Security / Compliance
- ✅ GitHub Copilot: FedRAMP High via GHE — preferred government option
- ✅ Amazon Q Developer: FedRAMP High via AWS GovCloud — strongest posture
- ✅ Windsurf FedRAMP: FedRAMP authorized (weakest capability)
- ⚠️ Claude Code: Not FedRAMP today; GovCloud roadmap in progress
- ❌ Devin, Cursor, Windsurf Pro: Not FedRAMP authorized

---

## Decision Required

### Recommended: Claude Code Ecosystem (Standard Environments)

**Best For:** All non-government-network development. Highest performance, reliability, and browser automation. Full agentic capability via CLI, MCP, and Chrome extension.

**Trade-off:** Not FedRAMP authorized. Cannot be used on government-classified networks today.

---

### Complementary: Cursor (IDE-First Teams)

**Best For:** Developers who prefer an IDE-native experience over terminal-first workflows. Use alongside Claude Code — Cursor for IDE editing, Claude Code for complex agentic tasks.

**Trade-off:** No browser automation; not FedRAMP authorized.

---

### Selective: Devin (Autonomous Task Execution)

**Best For:** Well-scoped, isolated feature builds or bug-fix sprints where developer time cost exceeds $500/month equivalent. Not a general-purpose replacement.

**Trade-off:** Very high cost, proprietary environment, no FedRAMP.

---

### Conditional: GitHub Copilot (FedRAMP — Preferred)

**Best For:** Government-network deployments where GHE is already licensed or where Microsoft infrastructure is preferred. Best compliance/capability trade-off for regulated environments.

**Trade-off:** Weak browser automation; GPT-4o model only.

---

### Conditional: Amazon Q Developer (FedRAMP — AWS Stacks)

**Best For:** AWS-centric teams requiring FedRAMP where GHE is not in use.

**Trade-off:** Poor general-purpose performance outside AWS ecosystem.

---

### Alternative: Windsurf Pro (Agent-First IDE)

**Best For:** Developers who want a fully integrated agentic IDE experience. Cascade provides genuine full agentic capability — terminal, multi-file edits, browser — with frontier models at $15/month. A strong peer to Cursor, not a downgrade from it.

**Windsurf Pro vs. Cursor — choose based on:**
- Windsurf Pro: prefer the agent-first Cascade flow, tighter built-in agentic loop, lower price
- Cursor: prefer maximum model flexibility, .cursorrules per-repo config, Composer multi-model switching

**Trade-off:** No MCP ecosystem, no mobile, not FedRAMP authorized.

---

### Last Resort: Windsurf FedRAMP

**Rationale:** Weakest capability of all options evaluated. Use only when GHE (Copilot) and Amazon Q are not viable and FedRAMP is a hard requirement.

---

## Credit Limits and Usage Caps

Understanding how each tool meters usage is critical for cost governance and for avoiding mid-session interruptions in agentic workflows.

| **Tool** | **Credit / Usage Model** | **What Happens When You Hit the Limit** | **Add-On Options** |
|---|---|---|---|
| **Claude Code** | API token-based (pay-as-you-go) | Requests fail until usage budget is increased or reset | Increase API spend limit anytime in Anthropic Console; no hard cap — governed by team budget policy |
| **Devin** | $500/seat/mo flat (ACUs — Agent Compute Units) | Task queue pauses; new tasks blocked until next cycle | Purchase additional ACUs from Cognition; expensive at scale |
| **Cursor** | $20/seat/mo; 500 fast requests/mo (GPT-4o/Sonnet); unlimited slow requests | Drops to slower model (no interruption, just slower) | No hard block; premium model requests throttle gracefully |
| **Windsurf Pro** | $15/seat/mo with 500 credits/mo; add-on credits available | Agent pauses / prompts to purchase credits | $10 for 250 credits (Pro); credits roll over — no expiry; Teams/Enterprise: $40 for 1,000 pooled credits |
| **GitHub Copilot** | Subscription-based; completions unlimited; agent mode has soft limits | May throttle chat/agent responses at high volume | Enterprise plan has higher limits; no per-token cost |
| **Amazon Q Developer** | Free tier: limited; $19/seat/mo Pro: higher limits | Free tier hits daily caps quickly on agent tasks | Upgrade to Pro for production use |
| **Windsurf FedRAMP** | Custom Enterprise pricing (Palantir FedStart); credit model same as commercial Enterprise | Custom SLA terms; credits governed by contract | Requires contract amendment to expand; slow procurement cycle |

### Key Insights

- **Claude Code has no hard credit cap** — usage is API cost-based, so teams set their own budget ceiling in the Anthropic Console. A developer doing heavy agentic work (Opus 4.6) will spend $100–200/month; lighter Sonnet-based use runs $20–50/month. Cost scales with output quality — the most capable model (Opus) costs ~5x more per token than Sonnet.

- **Windsurf Pro is the most flexible for individuals** — start at $15/month (500 credits), buy add-on 250-credit packs at $10 each as needed. Credits do not expire. For teams doing sustained agentic work, model to 1,500–2,000 credits/month per active developer.

- **Windsurf FedRAMP pricing is custom and significantly higher** than commercial plans. The FedRAMP-authorized Enterprise tier is delivered via Palantir FedStart and requires a government procurement contract. Expect ~$60–100+/user/month at minimum; actual cost requires direct quote. Factor in FedRAMP overhead, compliance fees, and slow add-on procurement — budget unpredictability is a real operational concern.

- **Cursor throttles gracefully** — when fast-request credits are exhausted, the tool falls back to slower model responses rather than blocking. This is the best end-user experience for credit exhaustion, though it can slow mid-session agentic tasks.

- **GitHub Copilot and Amazon Q** are subscription-flat with no per-token cost, making them the most predictable for finance, but their capability ceiling is fixed — you cannot spend more to get a better model or more throughput.

---

## Questions for Discussion

1. **Compliance Scope:** Which project environments require FedRAMP authorization?
2. **Network Boundaries:** Can Claude Code run on workstations that also access government systems, or must the tool itself be FedRAMP-authorized?
3. **GitHub Enterprise Status:** Is GHE already licensed? If yes, GitHub Copilot FedRAMP is the lowest-friction compliant option.
4. **AWS Stack:** Is the codebase AWS-centric? If yes, Amazon Q adds extra value for infrastructure work.
5. **Devin Pilot:** Is there budget to pilot Devin for a defined set of autonomous tasks to validate ROI at the $500/seat cost?
6. **Hybrid Model:** Can teams run Claude Code for standard work and a FedRAMP tool only for government-network sessions?
7. **Anthropic Roadmap:** Is waiting for Claude Code FedRAMP authorization a viable option given project timelines?

---

## Next Steps

**If Claude Code Approved (Standard Environments):**
1. Provision Anthropic API keys with usage budgets (Week 1)
2. Deploy Claude Code CLI + VS Code extension to developer machines (Week 1)
3. Configure Playwright MCP and Chrome extension for browser automation (Week 2)
4. Establish MCP server standards for team workflows (Week 2–3)
5. Evaluate Cursor as a complementary IDE tool for preference-based adoption (Week 3)
6. Track adoption and productivity metrics at Day 30 (Month 2)

**If FedRAMP Required (Government Networks):**
1. Confirm whether GitHub Enterprise is already licensed — if yes, activate Copilot FedRAMP immediately (Week 1)
2. If AWS-centric stack and no GHE: procure Amazon Q Developer via AWS GovCloud (Week 1–2)
3. If neither GHE nor AWS Q viable: proceed with Windsurf FedRAMP as interim (Week 2)
4. Document automation reliability gaps and manual fallbacks for any FedRAMP tool (Week 2)
5. Revisit when Claude Code FedRAMP authorization becomes available

**If Devin Pilot Approved:**
1. Define 3–5 well-scoped autonomous tasks for 30-day pilot (Week 1)
2. Assign Cognition AI seats and configure Slack integration (Week 1)
3. Measure output quality, autonomy rate, and developer time saved vs. cost (Month 1)
4. Make permanent adoption decision based on pilot ROI (Month 2)

---

*Document owner: REI Systems Engineering | Next review: 2026-06-01*
