---
name: architect
description: Produce a solution architecture via the solution-architect subagent — requirements, constraints, ranked quality attributes, 2–3 options, decision with explicit sacrifices across the seven owned domains (technology, pattern, cloud, integration, scalability, security, tradeoffs), components, data flow, identity/security, network, observability, deployment, failure modes, cost drivers, migration, and acceptance criteria. Read-only. Use BEFORE implementation when architecture is material.
argument-hint: "<system, feature, or decision to architect>"
disable-model-invocation: true
context: fork
agent: solution-architect
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /architect

Read-only. Produce a solution architecture the `developer`, `ai-engineer`, `devops-engineer`, and `qa-engineer` roles can build against without re-asking the user.

## Request
$ARGUMENTS

## Procedure
Follow the `solution-architect` skill method, then complete the architecture contract below (the skill's Owned Domain Decisions are its core; the remaining sections make it a deliverable):

1. **Requirements & constraints** — functional, non-functional (SLOs, data volume, latency, compliance), hard vs soft. Read the repo first: existing stack, IaC, manifests, ADRs. Do not redesign what already exists unless the request or a root cause demands it.
2. **Quality attributes ranked** (top 3) — drive every decision from this ranking.
3. **Options** — 2–3 viable architectures; for each: sketch, strengths, sacrifices, effort, reversibility.
4. **Decision** — one recommendation tied to constraints + ranking; every owned domain addressed or explicitly out of scope.
5. **Components & data flow** — responsibilities, contracts between components, sync vs async, ownership of data.
6. **Identity & security design** — authn/authz model, secret management, trust boundaries, PII handling, threat model summary (verification of the implementation is `security-reviewer`'s).
7. **Network** — exposure, private vs public paths, egress, boundaries.
8. **Observability** — logs/metrics/traces per component, SLO signals, alerting intent.
9. **Deployment & environments** — topology, promotion, IaC ownership (execution by `devops-engineer`).
10. **Failure modes** — top 5 with detection and degradation behavior.
11. **Cost drivers** — what scales with users/data/requests; rough order of magnitude, not fake precision.
12. **Migration / adoption path** — from current state, in reversible increments.
13. **Acceptance criteria** — measurable; consumed by `qa-engineer`.
14. **Load-bearing decisions** — most expensive to reverse; flag for early validation.

Split contracts: for vector DB, model-serving infra, or game engine choices, require the specialist requirements doc (`ai-engineer` / `game-developer`). If it does not exist, state that `/ai-design` (or `game-developer`) must run first and stop short of selecting the product.

## Output contract
The `solution-architect` skill's Required output format, extended with the sections above (use their names as `###` headings), and a final line:
`Next command: /ai-design | /plan-work | /build | /devops | /security — <reason>`

## Rules
- Every decision lists alternatives rejected and explicit sacrifices; "best practice" is not a rationale.
- Never invent services, limits, or pricing — verify via repo, official docs, or the `documentation` MCP; mark the rest "unverified".
- Do not implement. Read-only `Bash` (git, listing, manifests) only.
