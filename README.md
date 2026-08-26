# skill_ai — Claude Code Engineering OS

Personal Claude Code plugin for `rizalvalry`. Four layers, one rule: **no duplication of responsibility**. Commands express intent, subagents own roles, role skills hold the method, reference skills supply domain conventions, `CLAUDE.md` holds project facts, MCP reaches external systems. Rules of record: [`guidence/GUIDE.md`](guidence/GUIDE.md) and [`guidence/MCP-GUIDE.md`](guidence/MCP-GUIDE.md).

```
CLAUDE CODE
│
├── Commands / Skills  (user-invoked; intent + contract)
│   ├── /plan-work  /build  /fix  /hunt  /test  /refactor  /map  /trace
│   ├── /architect  /ai-design  /agent-audit  /rag  /prompt  /eval
│   └── /security  /devops  /gate
│
├── Specialist Subagents  (roles; read-only unless the role must write)
│   ├── planner · solution-architect · developer · bug-hunter · qa-engineer
│   ├── ai-engineer · security-reviewer · devops-engineer · gatekeeper
│   └── project-manager  (OWNER / orchestrator — the only one that spawns agents)
│
├── Project Context
│   ├── CLAUDE.md                      (this repo's constitution)
│   └── templates/CLAUDE.project.md    (constitution template for your projects)
│
├── Skills  (reference — domain conventions; inform, never decide)
│   └── backend · frontend · azure · ai-foundry · rag-patterns · database
│
└── MCP  (slots documented in mcp/README.md; .mcp.json.example is empty by policy)
    └── GitHub · Azure · Figma · database · documentation
```

## Commands

All commands are **user-invoked only** (`disable-model-invocation: true`) so they never double-trigger with the role skills, whose descriptions do the automatic routing. Invoke as `/skill-ai:<name>` (or `/<name>` when no other skill has that name).

| Command | Runs as | Contract (from `GUIDE.md` §4) | Next |
|---|---|---|---|
| `/plan-work <task>` | fork → `planner` | Deliverable-grade plan: scope, current-state evidence, affected files, ordered steps, testing, risks, rollback, completion criteria. Read-only. | `/architect` `/build` |
| `/build <feature>` | main session · `developer` | Implement a scoped feature: conventions first, lane (Fast/Full), impact + compat analysis, smallest diff, verification actually run, completion report. | `/test` `/gate` |
| `/fix <bug + evidence>` | main session · `developer` | Bounded bug with evidence: reproduce or state the mechanism, smallest repair, regression test, prediction validation. No evidence → routes to `/hunt`. | `/gate` |
| `/hunt <bug>` | fork → `bug-hunter` | Read-only root cause: symptom, evidence, hypotheses, counter-evidence, root cause (High confidence), validation predictions, observability gaps, fix spec. | `/fix` |
| `/test <design\|implement\|audit> <target>` | `qa-engineer` designs → main session implements | Smallest useful test set by risk; behavior over trivia; scenario→test mapping; acceptance evidence for `/gate`. | `/gate` |
| `/refactor <area + goal>` | main session · `developer` | Behavior-preserving: pin behavior first (characterization tests), contracts stable, small verified steps. | `/code-review` |
| `/map [focus]` | fork → `solution-architect` | Repository map: entry points, modules, data flows, runtime/deploy, tests, config, risk hotspots. | `/trace` `/plan-work` |
| `/trace <behavior>` | fork → `bug-hunter` | One behavior end-to-end with `file:line` per hop: validation → authz → domain → persistence → external → errors → result. | `/hunt` `/refactor` |
| `/architect <problem>` | fork → `solution-architect` | Options → decision with sacrifices across the 7 owned domains; components, data flow, identity, network, observability, deployment, failure modes, cost, migration, acceptance. | `/plan-work` `/build` |
| `/ai-design <feature>` | fork → `ai-engineer` | Is AI justified? If yes: model, tools, data, context/retrieval, orchestration, evals, guardrails, observability, cost; Retrieval/Serving Requirements for the architect. | `/architect` `/rag` `/eval` |
| `/agent-audit <agent>` | fork → `ai-engineer` | Audit an existing LLM agent: instruction hierarchy, tools, routing, authorization, grounding, memory, resilience, injection, observability, evals. | `/ai-design` `/fix` |
| `/rag <design\|audit\|debug> …` | fork → `ai-engineer` | Pipeline stages ingestion→…→evaluation; 13-class failure taxonomy; retrieval vs generation failure by evidence; Retrieval Requirements doc. | `/architect` `/eval` |
| `/prompt <prompt> [--rewrite]` | fork → `ai-engineer` | Provider-neutral prompt audit: ambiguity, conflicts, constraints, tool misuse, injection, grounding, schema, token waste, testability. Rewrite only on request. | `/eval` |
| `/eval <feature>` | fork → `ai-engineer` | Eval matrix: criteria, dataset, golden/edge/adversarial/injection/tool-failure/hallucination cases, scoring, thresholds, regression policy, release gate. | `/build` `/gate` |
| `/security [scope]` | fork → `security-reviewer` | Broad read-only audit: secrets + history, authn/authz, input/output, injection, dependencies, SSRF, data leakage, cloud, containers, CI/CD, AI boundaries. | `/fix` `/devops` |
| `/devops <diagnose\|design\|change\|review> …` | fork → `devops-engineer` | Pipeline/deploy analysis; any mutation returned as a **Change Plan** applied only after your confirmation. | `/security` `/gate` |
| `/gate <intended change>` | fork → `gatekeeper` | Independent go/no-go on evidence: PASS / PASS WITH CONDITIONS / FAIL with blockers. Reports, never repairs. | commit / PR |

### Names that differ from the shorthand — and why

| Shorthand | Here | Reason |
|---|---|---|
| `/plan` | `/plan-work` | `/plan` is the built-in Plan Mode toggle (`GUIDE.md` §3). |
| `/review` | *(not shipped)* | Use the built-in `/code-review`; shipping a second review skill would duplicate it and any user-level `/review` workflow. |
| `/agent` | `/agent-audit` | Avoids confusion with the built-in `/agents` manager and says what it does (audit, not build — build is `/ai-design`). |
| `rag` (reference skill) | `rag-patterns` | The command `/rag` owns the name `rag`. |

Built-ins this pack deliberately relies on instead of re-implementing: `/plan`, `/code-review`, `/security-review` (diff-scoped), `/verify`, `/debug`, `/run`, `/batch`, `/loop`, `/doctor`.

### Golden workflow

```
Requirement → /plan-work → /architect | /ai-design (when architecture is material)
→ /build | /fix → /test → /code-review → /security-review | /security → /verify → /gate → commit / PR / deploy
```

## Subagents

Every command that only reads runs `context: fork` into a specialist whose tools block `Edit`/`Write`/`NotebookEdit`/`Agent`, so read-only is enforced by tooling, not by prompting. Mutable commands stay in the main session (`GUIDE.md` §1). Each agent is a thin wrapper that preloads its role skill (`skills:`) — the skill remains the single source of truth for the method.

| Subagent | Model | Writes? | Preloads | Used by |
|---|---|---|---|---|
| `planner` | `opus` (pinned — documented decision) | no | `planner` | `/plan-work`, PM |
| `solution-architect` | `inherit` | no | `solution-architect` | `/architect`, `/map`, PM |
| `developer` | `sonnet` (pinned — documented decision) | **yes** (leaf; no `Agent`) | `developer` | `/build`, `/fix`, `/refactor`, `/test`, PM |
| `bug-hunter` | `inherit` | no | `bug-hunter` | `/hunt`, `/trace`, PM |
| `qa-engineer` | `inherit` | no | `qa-engineer` | `/test` (design), PM |
| `ai-engineer` | `inherit` | no | `ai-engineer` | `/ai-design`, `/rag`, `/prompt`, `/eval`, `/agent-audit`, PM |
| `security-reviewer` | `inherit` | no | `security-reviewer` | `/security`, PM |
| `devops-engineer` | `inherit` | no — returns a Change Plan | `devops-engineer` | `/devops`, PM |
| `gatekeeper` | `inherit` | no | — (contract in the agent) | `/gate` |
| `project-manager` | `opus` (pinned — documented decision) | governance artifacts only | `project-manager` | multi-skill requests; the **only** agent allowed to spawn agents |

Model policy: new agents default to `inherit` (`GUIDE.md` §14) so your active model/org policy stays authoritative. The three pins predate this restructure and keep their documented rationale (routing blast radius for PM, deep low-frequency reasoning for planner, fastest reliable implementer for developer); change a pin only with benchmark evidence.

`game-developer` and `ui-ux` remain skill-only roles (no subagent yet); the PM invokes them by name and states that the model is inherited.

## Responsibility Matrix (no duplication)

| Domain | Owner | Notes |
|---|---|---|
| Technology selection, architecture pattern, cloud strategy, integration strategy, scalability design, security design, tradeoff articulation | **solution-architect** | sole owner of the 7 domains |
| Task decomposition, sequencing, effort, per-task risk, handoff package | **planner** | never picks tech |
| Code implementation within a chosen stack | **developer** | never picks tech / architecture |
| Root cause investigation; end-to-end traces | **bug-hunter** | hands architectural causes to architect |
| Test strategy, scenarios, coverage gaps, acceptance evidence | **qa-engineer** | tests against architect's targets |
| Context engineering, retrieval/prompt/memory/agent-state strategy, model selection, eval design, grounding | **ai-engineer** | produces Retrieval + Serving Requirements → architect selects product/hosting |
| Vulnerability findings by evidence | **security-reviewer** | verifies implementation matches architect's security design |
| CI/CD, deployment execution, environment separation, secrets wiring, IaC/container hygiene, rollback | **devops-engineer** | plans; never applies without confirmation; platform choice is architect's |
| Independent release go/no-go | **gatekeeper** | reports blockers; never repairs |
| Design-side quality, design gaps, Figma handoff readiness | **ui-ux** | never verifies implementation (qa-engineer) |
| Gameplay architecture, content/animation pipelines, save schema, feel, debug strategy | **game-developer** | produces Engine Requirements → architect selects engine |
| Domain conventions (backend, frontend, azure, ai-foundry, rag-patterns, database) | **reference skills** | inform only; zero decisions |
| Intake routing, ownership arbitration, handoff enforcement, delegation, RAID, DoR/DoD, master ledger, status, go/no-go acceptance | **project-manager** | holds the ledger, never the pen |

**Rule:** a task touching more than one domain is routed so the OWNING role decides and the others consume via handoff. **Enforcer:** `project-manager`, whose authority is over WHO decides and WHEN work is accepted — never WHAT.

## Project context

- `CLAUDE.md` — this repository's constitution: layer model, invariants, how to add a command/role/reference skill, validation.
- `templates/CLAUDE.project.md` — copy to a target repo's `CLAUDE.md`: verified facts, run/test/lint commands, non-negotiable rules, the golden workflow, MCP table, pointer to `.claude/rules/`.
- `guidence/CLAUDE.user.template.md` — personal `~/.claude/CLAUDE.md` merge reference.

## MCP

`.mcp.json.example` is `{"mcpServers": {}}` on purpose: server commands, package names, and auth fields must be copied from each provider's current instructions, never guessed, and never committed with credentials. `mcp/README.md` maps the five slots — **GitHub** (PRs/CI for `/devops`, `/gate`, `/security`), **Azure** (`/architect`, `/devops`, `azure`/`ai-foundry` skills), **Figma** (`frontend`, `ui-ux`, design-to-code), **database** (read-only by default for `/trace`, `/hunt`, `database` skill), **documentation** (every role's grounding rule) — to the roles that use them and the access scope each may have.

## Install — Claude Code

```
/plugin marketplace add rizalvalry/skill_ai
/plugin install skill-ai@skill-ai
```

Update: `/plugin marketplace update skill-ai` then `/plugin install skill-ai@skill-ai`. If agents are not discovered after the first install, restart the session; skill edits reload with `/reload-skills`.

## Install — claude.ai

claude.ai uploads skills as ZIPs (agents and forked commands do not apply there). ZIP each `skills/<name>/` folder with `SKILL.md` at the ZIP root and upload via **Settings → Features → Skills**. Role and reference skills are the useful ones on claude.ai; command skills assume Claude Code.

## Validate before committing

```
python scripts/validate_pack.py
```

Frontmatter, name/directory match, duplicates, built-in collisions, fork→agent and agent→skill references, layer consistency, read-only tool blocks on analysis agents, manifest version match, secret-free MCP example, stale references.

## Repo layout

```
skill_ai/
├── .claude-plugin/          plugin.json · marketplace.json  (v1.0.0)
├── .mcp.json.example        {"mcpServers": {}} — by policy
├── CLAUDE.md                repo constitution
├── agents/                  10 subagents (thin wrappers; preload role skills)
├── guidence/                GUIDE.md · MCP-GUIDE.md · README.md · CLAUDE.user.template.md  (rules of record)
├── mcp/README.md            five MCP slots → roles → scope
├── scripts/validate_pack.py
├── skills/
│   ├── <17 commands>/       plan-work build fix hunt test refactor map trace architect ai-design agent-audit rag prompt eval security devops gate
│   ├── <11 roles>/          planner developer solution-architect bug-hunter qa-engineer ai-engineer security-reviewer devops-engineer project-manager game-developer ui-ux
│   └── <6 reference>/       backend frontend azure ai-foundry rag-patterns database
└── templates/CLAUDE.project.md
```

## Changelog

- **1.0.0** — Restructure into Commands / Subagents / Roles / Reference / Context / MCP per `guidence/GUIDE.md`. Added 17 commands, 7 subagents (`solution-architect`, `bug-hunter`, `qa-engineer`, `ai-engineer`, `security-reviewer`, `devops-engineer`, `gatekeeper`), `devops-engineer` role skill, 6 reference skills, `CLAUDE.md`, project template, MCP layer docs, validator. **Breaking:** `qa-analysis` renamed to `qa-engineer`.
- 0.6.0 — developer skill v4.0 (lane-based execution).
- 0.5.x — production intelligence patterns; `security-reviewer` skill; `project-manager` OWNER skill + Opus-pinned subagent.

## License

MIT
