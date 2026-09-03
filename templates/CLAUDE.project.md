# <Project name> — Claude Code project constitution

Copy this file to `<repo>/CLAUDE.md`, fill every `<...>`, delete sections that do not apply. Keep it short: facts and non-negotiable rules only. Procedures belong in skills; enforcement belongs in hooks.

## Facts (verified, not aspirational)

- **Purpose:** <one sentence — what this system does and for whom>
- **Stack (decided by solution-architect — do not re-decide):** <language/runtime · framework · database · queue/cache · cloud · IaC>
- **Repository layout:** <top-level dirs and what lives where>
- **Environments:** <dev · staging · prod — how they differ, what is never touched from a dev session>
- **Run locally:** `<command>`
- **Test:** `<command>` (unit) · `<command>` (integration) · `<command>` (e2e)
- **Lint / typecheck:** `<command>`
- **Build / deploy:** `<command or pipeline name>` — deploys are performed by <CI / humans>, never from a Claude session
- **Observability:** <where logs/metrics/traces go; how to query them>

## Non-negotiable rules

1. Never commit secrets; configuration comes from `<env / secret store>`; `.env*` files are never committed.
2. Public contracts (`<API schemas / event payloads / DB schema>`) change only with a compatibility plan and explicit approval.
3. Migrations: <expand/contract policy, tool, where they live, rollback requirement>.
4. Every bug fix ships with a regression test; every feature ships with tests at the level that proves the behavior.
5. Authorization is enforced in `<layer/module>` — never by prompts, never only in the UI.
6. <Domain rule 1 — e.g. money is integer minor units; timestamps are UTC>
7. <Domain rule 2>

## Conventions

- Code style: `<formatter/linter>` decides; do not argue with it.
- Naming / module boundaries: <one or two lines>
- Error handling: <typed errors · where they are mapped to responses · logging rule>
- Logging: structured, correlation ID `<field>`, credentials and PII masked by `<mechanism>`.
- Tests: <framework · fixtures/factories location · mocking boundary rule>

## Workflow with the skill-ai plugin

Use built-ins when they solve it: `/plan` (Plan Mode), `/code-review`, `/security-review` (diff), `/verify`, `/debug`, `/run`.

Golden path for non-trivial work:
`/plan-work` → `/architect` or `/ai-design` (when architecture is material) → `/build` or `/fix` → `/test` → `/code-review` → `/security-review` or `/security` → `/verify` → `/gate` → commit / PR.

Read-only first when unsure: `/analyze` (health baseline), `/map` (repo), `/trace <behavior>`, `/hunt <bug>`.
Pipelines and infra: `/devops` returns a Change Plan (read-only fork); `/devops-apply` applies it in the main session after confirming environment and every file with you.

## Path-scoped rules

Put topic-specific rules in `.claude/rules/*.md` (e.g. `database.md`, `frontend.md`, `pipelines.md`) rather than growing this file.

## MCP servers used by this project

| Server | Purpose | Scope | Notes |
|---|---|---|---|
| `<github>` | PRs, issues, CI status | read for analysis; write only for PR/issue actions the task requires | auth via <OAuth/token env var> |
| `<database>` | schema inspection, read-only queries | read-only | never point at production from a dev session |
| `<documentation>` | current library/cloud docs | read-only | prefer over memory for API specifics |

Credentials never live in `.mcp.json`; use the mechanism the server documents.

## Known constraints / open decisions

- <constraint or pending decision — owner — date>
