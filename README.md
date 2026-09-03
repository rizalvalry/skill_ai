# skill_ai — Claude Code Engineering OS

Personal Claude Code plugin for `rizalvalry`. Four layers, one rule: **no duplication of responsibility**. Commands express intent, subagents own roles, role skills hold the method, reference skills supply domain conventions, `CLAUDE.md` holds project facts, MCP reaches external systems. Rules of record: [`guidence/GUIDE.md`](guidence/GUIDE.md) and [`guidence/MCP-GUIDE.md`](guidence/MCP-GUIDE.md).

```
CLAUDE CODE
│
├── Commands / Skills  (user-invoked; intent + contract)
│   ├── /plan-work  /build  /fix  /hunt  /test  /refactor  /map  /analyze  /trace
│   ├── /architect  /ai-design  /agent-audit  /rag  /prompt  /eval
│   └── /security  /devops  /devops-apply  /gate
│
├── Specialist Subagents  (roles; read-only unless the role must write)
│   ├── planner · solution-architect · developer · bug-hunter · qa-engineer
│   ├── ai-engineer · security-reviewer · devops-engineer · gatekeeper · workspace-analyst
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

All commands are **user-invoked only** (`disable-model-invocation: true`): their descriptions are not loaded into the model's context, so they never double-trigger with the role skills, whose descriptions do the automatic routing. Invoke as `/skill-ai:<name>` (or `/<name>` when no other skill has that name).

| Command | Runs as | Contract (from `GUIDE.md` §4) | Next |
|---|---|---|---|
| `/plan-work <task>` | fork → `planner` | Deliverable-grade plan: scope, current-state evidence, affected files, ordered steps, testing, risks, rollback, completion criteria. Read-only. | `/architect` `/build` |
| `/build <feature>` | main session · `developer` skill | Implement a scoped feature: conventions first, lane (Fast/Full), impact + compat analysis, smallest diff, verification actually run, completion report. | `/test` `/gate` |
| `/fix <bug + evidence>` | main session · `developer` skill | Bounded bug with evidence: reproduce or state the mechanism, smallest repair, regression test, prediction validation. No evidence → routes to `/hunt`. | `/gate` |
| `/hunt <bug>` | fork → `bug-hunter` | Read-only root cause: symptom, evidence, hypotheses, counter-evidence, root cause (High confidence), validation predictions, observability gaps, fix spec. | `/fix` |
| `/test <design\|implement\|audit> <target>` | `qa-engineer` subagent designs → main session implements | Smallest useful test set by risk; behavior over trivia; scenario→test mapping; acceptance evidence for `/gate`. | `/gate` |
| `/refactor <area + goal>` | main session · `developer` skill | Behavior-preserving: pin behavior first (characterization tests), contracts stable, small verified steps. | `/code-review` |
| `/map [focus]` | fork → `solution-architect` | Repository map: entry points, modules, data flows, runtime/deploy, tests, config, risk hotspots. | `/trace` `/plan-work` |
| `/analyze [scope] [--quick\|--deep] [--allow-network] [--no-run] [--no-save] [--out <file>]` | `workspace-analyst` subagent analyzes (read-only) → main session saves the report to `docs/analysis/` | **Workspace Analysis Report**, no assumptions (every statement `file:line` or `Not verified`): technical stack, architecture topology + Mermaid diagram, business domain & processes with rules as coded, operational + delivery workflows, user flows + permission matrix per actor; then health scorecard with confidence, churn × size hotspots, technical-debt register, top-5 action plan routed to owners, trend vs previous report. Never redesigns, diagnoses, states business intent, or fixes. | `/plan-work` `/security` `/refactor` |
| `/trace <behavior>` | fork → `bug-hunter` | One behavior end-to-end with `file:line` per hop: validation → authz → domain → persistence → external → errors → result. | `/hunt` `/refactor` |
| `/architect <problem>` | fork → `solution-architect` | Options → decision with sacrifices across the 7 owned domains; components, data flow, identity, network, observability, deployment, failure modes, cost, migration, acceptance. | `/plan-work` `/build` |
| `/ai-design <feature>` | fork → `ai-engineer` | Is AI justified? If yes: model, tools, data, context/retrieval, orchestration, evals, guardrails, observability, cost; Retrieval/Serving Requirements for the architect. | `/architect` `/rag` `/eval` |
| `/agent-audit <agent>` | fork → `ai-engineer` | Audit an existing LLM agent: instruction hierarchy, tools, routing, authorization, grounding, memory, resilience, injection, observability, evals. | `/ai-design` `/fix` |
| `/rag <design\|audit\|debug> …` | fork → `ai-engineer` | Pipeline stages ingestion→…→evaluation; 13-class failure taxonomy; retrieval vs generation failure by evidence; Retrieval Requirements doc. | `/architect` `/eval` |
| `/prompt <prompt> [--rewrite]` | fork → `ai-engineer` | Provider-neutral prompt audit: ambiguity, conflicts, constraints, tool misuse, injection, grounding, schema, token waste, testability. Rewrite only on request. | `/eval` |
| `/eval <feature>` | fork → `ai-engineer` | Eval matrix: criteria, dataset, golden/edge/adversarial/injection/tool-failure/hallucination cases, scoring, thresholds, regression policy, release gate. | `/build` `/gate` |
| `/security [scope]` | fork → `security-reviewer` | Broad read-only audit: secrets + history, authn/authz, input/output, injection, dependencies, SSRF, data leakage, cloud, containers, CI/CD, AI boundaries. Size-gated with `Not verified`. | `/fix` `/devops` |
| `/devops <diagnose\|design\|change\|review> …` | fork → `devops-engineer` | Pipeline/deploy analysis; any mutation returned as a **Change Plan** — never applied by the fork. | `/devops-apply` `/security` |
| `/devops-apply <plan>` | main session · `developer` skill | Applies a `/devops` Change Plan: refuses plans without environment/rollback/verification, confirms every file with you, runs pre-checks, applies diff-first, verifies. Never deploys unless you ask for that exact step. | `/security` `/gate` |
| `/gate <intended change>` | fork → `gatekeeper` | Independent go/no-go on evidence: PASS / PASS WITH CONDITIONS / FAIL with blockers. Reports, never repairs. | commit / PR |

### GUIDE.md §4 names → plugin names

| In `GUIDE.md` | Here | Reason |
|---|---|---|
| `/plan-work` | `/plan-work` | Kept as in `GUIDE.md`: `/plan` is the built-in Plan Mode toggle (`GUIDE.md` §3), so the shorthand `/plan` is not available. |
| `/review` | *(not shipped)* | Use the built-in `/code-review`; a second review skill would duplicate it and any user-level `/review` workflow. |
| `/agent-audit` | `/agent-audit` | Kept long: `/agent` would collide with the built-in `/agents` manager and hide that it audits (building is `/ai-design`). |
| `/test-work` | `/test` | Shorter; no built-in `/test` exists. |
| `/map-codebase` | `/map` | Shorter; no collision. |
| `/prompt-audit` | `/prompt` | Shorter; no collision. |
| `/eval-ai` | `/eval` | Shorter; no collision. |
| `/security-audit` | `/security` | Shorter; the built-in is `/security-review` (diff-scoped), which this complements. |
| — | `/devops-apply` | Added: the apply half of `/devops` must run in the main session (a fork cannot edit and its body never reaches the main session). |
| — | `/analyze` | Added: the saved Workspace Analysis Report (as-is stack, topology, business processes, workflows, user flows, then health grading and a debt register) has no `GUIDE.md` §4 counterpart; `/map` is module-level reconnaissance for engineers, `/analyze` is the system-level report and its persistence needs the main session. |
| `rag` (reference) | `rag-patterns` | The command `/rag` owns the name `rag`. |

Not shipped from `GUIDE.md` §4 (by design — outside this pack's scope): `/do`, `/api-audit`, `/db`, `/cloud-audit`, `/clarify`, `/scope`, `/estimate`, `/proposal`, `/docs-work`, and the `sidejob-analyst` agent. Built-ins this pack deliberately relies on instead of re-implementing: `/plan`, `/code-review`, `/security-review`, `/verify`, `/debug`, `/run`, `/batch`, `/loop`, `/doctor`.

### Golden workflow

```
Requirement → /plan-work → /architect | /ai-design (when architecture is material)
→ /build | /fix → /test → /code-review → /security-review | /security → /verify → /gate → commit / PR / deploy
Pipelines/infra: /devops (plan, read-only fork) → /devops-apply (confirm + apply, main session) → /security → /gate
Inherited or unfamiliar workspace: /analyze (health baseline) → /map (topology) → /plan-work <remediation> → the owning command per register row
```

## Subagents

Every command that only reads runs `context: fork` into a specialist subagent. Plugin agents are registered as `skill-ai:<name>` — that is the `agent:` value in forked commands and the `subagent_type` the PM uses.

**What is enforced by tooling vs by prompt — read this honestly:**

- Tool-blocked on every analysis agent: `Edit`, `Write`, `NotebookEdit`, `Agent` (no fan-out), `Artifact`, `WebFetch`, `WebSearch` (no exfiltration channel for injected content). The validator fails the build if any is missing.
- **Not** tool-blocked: `Bash`. Every analysis agent's body restricts it to inspection (`git log/diff`, running existing tests, read-only queries), and every agent treats retrieved content as data — but that is prompt-level. Residual risk: a sufficiently persuasive injected instruction could still run a shell command. If you run these forks on untrusted repositories, add deny rules in your project or user `settings.json`, e.g. `"deny": ["Bash(git push*)", "Bash(git commit*)", "Bash(rm *)", "Bash(sed -i*)", "Bash(* > *)"]`, or a `PreToolUse` hook (`GUIDE.md` §12).

Mutable commands (`/build`, `/fix`, `/refactor`, `/test` phase B, `/devops-apply`) stay in the main session and load the `developer` **skill** — they do not fork to the `developer` subagent. `/analyze` follows the `/test` shape: the read-only `workspace-analyst` subagent produces the report, the main session writes exactly one file under `docs/analysis/` (never overwriting, never committing). Each agent is a thin wrapper that preloads its role skill (`skills:`) — the skill remains the single source of truth for the method.

| Subagent | Model | Writes? | Preloads | Used by |
|---|---|---|---|---|
| `planner` | `opus` (pinned — documented decision) | no | `planner` | `/plan-work`, PM |
| `solution-architect` | `inherit` | no | `solution-architect` | `/architect`, `/map`, PM |
| `developer` | `sonnet` (pinned — documented decision) | **yes** (leaf; no `Agent`) | `developer` | PM delegation only — the mutable commands use the skill in-session |
| `bug-hunter` | `inherit` | no | `bug-hunter` | `/hunt`, `/trace`, PM |
| `qa-engineer` | `inherit` | no | `qa-engineer` | `/test` (design phase), PM |
| `ai-engineer` | `inherit` | no | `ai-engineer` | `/ai-design`, `/rag`, `/prompt`, `/eval`, `/agent-audit`, PM |
| `security-reviewer` | `inherit` | no | `security-reviewer` | `/security`, PM |
| `devops-engineer` | `inherit` | no — returns a Change Plan | `devops-engineer` | `/devops`, PM |
| `gatekeeper` | `inherit` | no | — (contract in the agent) | `/gate` |
| `workspace-analyst` | `inherit` | no — the main session saves its report | `workspace-analyst` | `/analyze` (Phase A), PM |
| `project-manager` | `opus` (pinned — documented decision) | governance artifacts only (`docs/v1/list-task.md`, `docs/pm/*`) | `project-manager` | multi-skill requests; the **only** agent allowed to spawn agents (never another PM) |

Model policy: new agents default to `inherit` (`GUIDE.md` §14) so your active model/org policy stays authoritative. The three pins predate this restructure and keep their documented rationale (routing blast radius for PM, deep low-frequency reasoning for planner, fastest reliable implementer for developer); change a pin only with benchmark evidence.

`game-developer` and `ui-ux` remain skill-only roles (no subagent yet); the PM invokes them by name and states that the model is inherited.

Role skills that keep their own task list (`ai-engineer`'s `list-task.md`) skip that step when running as a read-only fork; the main session or the PM owns the ledger.

## Responsibility Matrix (no duplication)

| Domain | Owner | Notes |
|---|---|---|
| Technology selection, architecture pattern, cloud strategy, integration strategy, scalability design, security design, tradeoff articulation; read-only repository maps | **solution-architect** | sole owner of the 7 domains |
| Task decomposition, sequencing, effort, per-task risk, handoff package | **planner** | never picks tech |
| Code implementation within a chosen stack | **developer** | never picks tech / architecture |
| Root cause investigation; end-to-end behavior traces | **bug-hunter** | hands architectural causes to architect |
| Test strategy, scenarios, coverage gaps, acceptance evidence | **qa-engineer** | tests against architect's targets |
| Context engineering, retrieval/prompt/memory/agent-state strategy, model selection, eval design, grounding; audits of existing agents and prompts | **ai-engineer** | produces Retrieval + Serving Requirements → architect selects product/hosting |
| Vulnerability findings by evidence — code, config, secrets history, dependencies, infra/IaC, CI/CD, containers, AI boundaries | **security-reviewer** | verifies implementation matches architect's security design |
| CI/CD, deployment execution, environment separation, secrets wiring, IaC/container hygiene, rollback | **devops-engineer** | plans; `/devops-apply` applies after confirmation; platform choice is architect's |
| Independent release go/no-go | **gatekeeper** | reports blockers; never repairs |
| Workspace Analysis Report — as-is technical stack, architecture topology, business domain & processes, workflows, user flows documented from code; health scorecard, hotspots, technical-debt register, action plan, trend | **workspace-analyst** | Observed evidence only, no hedging; routes every row to its owner; never redesigns (architect), diagnoses (bug-hunter), states intent (business-analyst), or confirms exploits (security-reviewer) |
| Design-side quality, design gaps, Figma handoff readiness | **ui-ux** | never verifies implementation (qa-engineer) |
| Gameplay architecture, content/animation pipelines, save schema, feel, debug strategy | **game-developer** | produces Engine Requirements → architect selects engine |
| Domain conventions (backend, frontend, azure, ai-foundry, rag-patterns, database) | **reference skills** | inform only; zero decisions |
| Intake routing, ownership arbitration, handoff enforcement, delegation, RAID, DoR/DoD, master ledger, status, go/no-go acceptance | **project-manager** | holds the ledger, never the pen |

**Rule:** a task touching more than one domain is routed so the OWNING role decides and the others consume via handoff. **Enforcer:** `project-manager`, whose authority is over WHO decides and WHEN work is accepted — never WHAT.

## Project context

- `CLAUDE.md` — this repository's constitution: layer model, invariants, how to add a command/role/reference skill, validation.
- `templates/CLAUDE.project.md` — copy to a target repo's `CLAUDE.md`: verified facts, run/test/lint commands, non-negotiable rules, the golden workflow, MCP table, pointer to `.claude/rules/`.
- `guidence/CLAUDE.user.template.md` — personal `~/.claude/CLAUDE.md` merge reference.
- Skills and agents reference the rulebook as `${CLAUDE_PLUGIN_ROOT}/guidence/GUIDE.md` so the path resolves inside the installed plugin, not in your project.

## MCP

`.mcp.json.example` is `{"mcpServers": {}}` on purpose: server commands, package names, and auth fields must be copied from each provider's current instructions, never guessed, and never committed with credentials (`.gitignore` excludes a real `.mcp.json`). `mcp/README.md` maps the five slots — **GitHub** (PRs/CI for `/devops`, `/gate`, `/security`), **Azure** (`/architect`, `/devops`, `azure`/`ai-foundry` skills), **Figma** (`frontend`, `ui-ux`, design-to-code), **database** (read-only by default for `/trace`, `/hunt`, `database` skill), **documentation** (every role's grounding rule) — to the roles that use them and the access scope each may have.

## Install — Claude Code

```
/plugin marketplace add rizalvalry/skill_ai
/plugin install skill-ai@skill-ai
```

Update to a newer version: `claude plugin marketplace update skill-ai` then `claude plugin update skill-ai@skill-ai` (or the same via `/plugin`), then restart the session so new agents are discovered; skill-only edits reload with `/reload-plugins`.

**Post-install smoke test (do this once after every agent change):** run `/skill-ai:gate <any small change>` and confirm the fork ran as the plugin agent (it reports read-only, produces the `Verdict` contract, and cannot edit), then `/skill-ai:test design <any module>` and confirm `subagent_type: skill-ai:qa-engineer` resolved. If a fork reports that `agent: skill-ai:<name>` could not be resolved, the `agent:` field wants the bare name in your Claude Code version — change the 13 forked commands accordingly and open an issue; static review cannot settle this.

## Install — claude.ai

claude.ai uploads skills as ZIPs (agents and forked commands do not apply there). ZIP each `skills/<name>/` folder with `SKILL.md` at the ZIP root and upload via **Settings → Features → Skills**. Role and reference skills are the useful ones on claude.ai; command skills assume Claude Code.

## Validate before committing

```
python scripts/validate_pack.py
claude plugin validate .
```

`validate_pack.py` checks frontmatter, name/directory match, duplicates, built-in collisions, fork→agent (namespaced) and agent→skill references, layer rules, the read-only tool block on analysis agents, `${CLAUDE_PLUGIN_ROOT}` on rulebook references, manifest version match, a secret-free empty MCP example, and stale identifiers. `claude plugin validate` checks the manifests and component frontmatter against Claude Code's own schema.

## Repo layout

```
skill_ai/
├── .claude-plugin/          plugin.json · marketplace.json  (v1.4.0)
├── .gitignore               __pycache__ · .mcp.json · personal notes
├── .mcp.json.example        {"mcpServers": {}} — by policy
├── CLAUDE.md                repo constitution
├── agents/                  11 subagents (thin wrappers; preload role skills)
├── guidence/                GUIDE.md · MCP-GUIDE.md · README.md (upstream, annotated) · CLAUDE.user.template.md
├── mcp/README.md            five MCP slots → roles → scope
├── scripts/validate_pack.py
├── skills/
│   ├── <19 commands>/       plan-work build fix hunt test refactor map analyze trace architect ai-design agent-audit rag prompt eval security devops devops-apply gate
│   ├── <12 roles>/          planner developer solution-architect bug-hunter qa-engineer ai-engineer security-reviewer devops-engineer project-manager game-developer ui-ux workspace-analyst
│   └── <6 reference>/       backend frontend azure ai-foundry rag-patterns database
└── templates/CLAUDE.project.md
```

## Changelog

- **1.4.0** — `/analyze` now delivers a saved **Workspace Analysis Report** (`docs/analysis/<date>-workspace-analysis.md`): the `workspace-analyst` v2 role documents the as-is system from code — technical stack, architecture topology with Mermaid diagram, business domain and processes with rules as coded, operational and delivery workflows, user flows and permission matrix per actor — before the health scorecard, hotspots, debt register, and action plan. "Tegas" report language rule: no hedging words in §1–§8, every statement `file:line` or `Not verified`, "Not found in code" as the only negative. Command changed from a fork to the `/test` shape (read-only subagent analyzes, main session writes one file); new `--no-save` and `--out` flags.
- **1.3.0** — New `/analyze` command with the `workspace-analyst` role skill and read-only subagent: workspace inventory (single repo / monorepo / multi-project), ten-dimension health scorecard graded from Observed evidence with confidence ratings, churn × size hotspots, technical-debt register with a route per row, top-5 action plan, trend against a previous `docs/analysis/` report, `--quick|--deep|--allow-network|--no-run` depth and command policy. PM ledger, routing table, handoff checklist, and pinning table extended; `/map` and the project template point to it.
- **1.0.1** — Review fixes (QA-1 functional, QA-2 security/performance, Final Reviewer): plugin-namespaced agent references (`skill-ai:<name>`); rulebook paths via `${CLAUDE_PLUGIN_ROOT}`; `/devops-apply` added so apply-side safeguards run in the main session; read-only agents also block `Artifact`/`WebFetch`/`WebSearch`; honest statement of the `Bash` residual risk; `ai-engineer` task-tracking step skipped in read-only forks; PM ledger path unified (`docs/v1/list-task.md`), pinning table and handoff checklist completed for all roles; `/test`/`/refactor` completion contracts completed; `git bisect` guarded; `/security` size gate and transcript-safe secret search; `.gitignore`; validator hardening.
- **1.0.0** — Restructure into Commands / Subagents / Roles / Reference / Context / MCP per `guidence/GUIDE.md`. Added 17 commands, 7 subagents, `devops-engineer` role skill, 6 reference skills, `CLAUDE.md`, project template, MCP layer docs, validator. **Breaking:** `qa-analysis` renamed to `qa-engineer`.
- 0.6.0 — developer skill v4.0 (lane-based execution); v4.2 later streamlined the hot path to adaptive single-agent execution and made `developer-reader` opt-in.
- 0.5.x — production intelligence patterns; `security-reviewer` skill; `project-manager` OWNER skill + Opus-pinned subagent.

## License

MIT
