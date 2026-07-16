# skill_ai

Personal Claude skills for `rizalvalry`. Works in both **Claude Code** and **claude.ai**.

## Skills

| Name | Purpose |
|------|---------|
| `planner` | Break tasks into dependency-aware execution plans |
| `developer` | Implement code that fits the codebase, minimal surgical changes |
| `solution-architect` | Design system architecture with explicit tradeoffs |
| `bug-hunter` | Diagnose root causes through hypothesis-driven investigation |
| `qa-analysis` | Design test plans and enumerate edge cases |
| `ai-engineer` | Build LLM/AI features with evals and grounding |
| `game-developer` | Implement game systems, engines, gameplay mechanics |

## Responsibility Matrix (no duplication)

Each skill has explicit ownership. Skills hand off across the boundary instead of duplicating work.

| Domain | Owner | Notes |
|--------|-------|-------|
| Technology selection (lang / framework / DB / lib / vector DB / queue) | **solution-architect** | sole owner |
| Architecture pattern (monolith / microservices / event-driven / CQRS) | **solution-architect** | sole owner |
| Cloud strategy (provider / region / IaC) | **solution-architect** | sole owner |
| Integration strategy (API contracts / sync vs async / gateway / broker) | **solution-architect** | sole owner |
| Scalability design (sharding / caching layers / autoscaling) | **solution-architect** | sole owner |
| Security design (auth / encryption / secrets / threat model) | **solution-architect** | sole owner |
| Tradeoff articulation (alternatives + sacrifices) | **solution-architect** | sole owner |
| Task decomposition, sequencing, handoff routing | **planner** | reads constraints; never picks tech |
| Code implementation within a chosen stack | **developer** | never picks tech / architecture |
| Root cause investigation (unknown bugs) | **bug-hunter** | hands off arch-level fixes to architect |
| Test strategy, scenarios, risk prioritization | **qa-analysis** | tests against architect's targets |
| Context engineering, retrieval strategy, prompt, memory, agent state, model selection, eval, grounding, failure-mode mitigation | **ai-engineer** | produces *Retrieval Requirements* doc → architect consumes for vector DB selection |
| Vector DB product + hosting selection | **solution-architect** | consumes ai-engineer's Retrieval Requirements |
| Game loop, FSM/ECS, physics, rendering, content pipeline, animation, asset streaming, save schema + migration, data-driven design, gameplay feel, debug strategy | **game-developer** | produces *Engine Requirements* doc → architect consumes for engine selection |
| Game engine product + tooling + platform + cloud services | **solution-architect** | consumes game-developer's Engine Requirements |

**Rule:** If a task touches >1 domain, the OWNING skill produces decisions and the others consume them via handoff. No skill makes decisions outside its owned column.

## Install — Claude Code (CLI)

Two steps. The first registers the repo as a marketplace; the second installs the plugin from it.

```
/plugin marketplace add rizalvalry/skill_ai
/plugin install skill-ai@skill-ai
```

After install, skills auto-trigger based on their `description`. To invoke explicitly, mention the skill by name in your message.

To update later: `/plugin marketplace update skill-ai` then `/plugin install skill-ai@skill-ai`.

### Use on any device (account-synced workflow)

The marketplace source is a Git URL, so re-running the same 2 commands on a new machine (after `claude login` with your account) pulls the same skills. No per-skill copy needed.

## Install — claude.ai (web / desktop, account-synced)

claude.ai uploads skills as individual ZIPs.

1. ZIP each skill folder separately: `skills/planner/` → `planner.zip` (the ZIP root must contain `SKILL.md` directly).
2. Go to **claude.ai → Settings → Features → Skills → Upload**.
3. Repeat for each skill.
4. Once uploaded, skills are tied to your account and available on any device after login.

## Edit a skill

Each skill is a single `SKILL.md` at `skills/<name>/SKILL.md`. Edit, commit, and:

- **Claude Code**: pulls on next `/plugin update`
- **claude.ai**: re-zip the folder and re-upload (replaces the previous version)

## Repo layout

```
skill_ai/
├── .claude-plugin/
│   ├── marketplace.json     # Marketplace catalog (referenced by /plugin marketplace add)
│   └── plugin.json          # Plugin manifest (auto-discovers ./skills/ and ./agents/)
├── skills/
│   ├── planner/SKILL.md
│   ├── developer/SKILL.md
│   ├── solution-architect/SKILL.md
│   ├── bug-hunter/SKILL.md
│   ├── qa-analysis/SKILL.md
│   ├── ai-engineer/SKILL.md
│   └── game-developer/SKILL.md
├── agents/
│   ├── planner.md           # Opus-pinned subagent wrapping the planner skill (model: opus)
│   └── developer.md         # Sonnet-pinned subagent wrapping the developer skill (model: sonnet)
├── README.md
└── LICENSE
```

## Subagents (model-pinned)

Skills (SKILL.md) have no `model` field — they run on whatever model the caller happens to be using. The `agents/` folder ships real Claude Code subagents that pin a specific model per role, so delegation via the Agent/Task tool's `subagent_type` is deterministic regardless of the caller's active model:

| Subagent | Model | Why | Tools |
|---|---|---|---|
| `planner` | `opus` | Deep, low-frequency reasoning (decomposition, risk, handoff design) justifies the slowest/most capable model. | Read-only — disallows `Edit`/`Write`/`NotebookEdit`/`Agent`; produces a plan, never code. |
| `developer` | `sonnet` | Fastest model that still reliably meets the production-grade bar this skill requires (impact analysis, backward-compat checks, verification checklist). Haiku is deliberately not used here — it under-performs on this skill's multi-step reasoning, and any speed gained would be lost to QA/Final Review rework. | Full read/write/execute — only disallows `Agent`, so it stays a leaf worker and hands off by name instead of spawning further agents. |

Both preload their matching skill's full method via the `skills:` frontmatter field, so the agent file itself stays a thin wrapper — the skill is still the single source of truth for the method.

## License

MIT
