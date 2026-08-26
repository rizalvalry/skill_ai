---
name: map
description: Read-only repository reconnaissance via the solution-architect subagent — entry points, modules and boundaries, data flows, runtime and deployment shape, tests, external dependencies, configuration surface, and risk hotspots — grounded in files actually read. Use when joining an unfamiliar codebase, before /plan-work or /architect on a large change, or when onboarding documentation is missing.
argument-hint: "[area or question to focus on — optional]"
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

# /map

Read-only repository map. Describe what IS, not what should be — no redesign, no recommendations beyond flagged risks. This is reconnaissance for `/plan-work`, `/architect`, `/trace`, and `/hunt`.

## Focus
$ARGUMENTS

(If empty: map the whole repository at module level.)

## Procedure
1. **Orient** — read manifests (package/build files, lockfiles, Docker/Compose, IaC, CI workflows), top-level README/CLAUDE.md, and `git log --oneline -30` for recent activity hotspots.
2. **Entry points** — executables, HTTP/gRPC routers, CLI commands, scheduled jobs, message consumers, UI roots. Cite `file:line`.
3. **Modules & boundaries** — the real module graph (imports/dependencies), layering (or its absence), shared kernels, cross-cutting concerns. Flag cycles.
4. **Data flows** — for the 3–5 most important behaviors: entry → validation → domain → persistence → external calls → response. One line each; deep traces belong to `/trace`.
5. **Persistence & integrations** — databases, schemas/migrations location, queues, caches, third-party APIs, auth providers, where credentials are expected to come from (names only).
6. **Runtime & deployment** — how it builds, runs locally, is tested, is deployed, is observed (logs/metrics/traces).
7. **Tests** — location, types present, apparent coverage of the critical flows, how to run them.
8. **Configuration surface** — env vars/config files/feature flags and which modules read them.
9. **Risk hotspots** — high churn × high complexity files, untested critical paths, security-sensitive surfaces (auth, secrets, uploads, external input), single points of failure, unclear ownership. Evidence for each.

## Output contract
```
### Repository at a glance      (stack, size, age, recent activity — 5 bullets max)
### Entry points                (table: kind · location · what it starts)
### Module map                  (tree or table + boundary/cycle notes)
### Key data flows              (3–5 one-line flows with file:line hops)
### Persistence & integrations
### Runtime, build, deploy, observe
### Tests                       (where, types, how to run, visible gaps)
### Configuration surface
### Risk hotspots               (table: hotspot · evidence · why it matters)
### Not inspected               (what you did not read and why)
Next command: /trace <flow> | /plan-work | /architect | /hunt — <reason>
```

## Rules
- Every claim cites a file you read. No inferred architecture from folder names alone.
- Do not propose changes; flag risks only.
- Read-only: `Bash` for listing, `git log`, reading manifests, running existing read-only scripts only.
