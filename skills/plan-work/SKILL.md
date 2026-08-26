---
name: plan-work
description: Produce a deliverable-grade, read-only implementation plan — scope, current-state evidence, affected files/components, ordered dependency-aware steps, testing, risks, rollback, and completion criteria — via the planner subagent. Use instead of the built-in /plan (Plan Mode) when you want a written plan artifact that downstream commands (/architect, /build, /fix, /test) can consume.
argument-hint: "<task or feature to plan>"
disable-model-invocation: true
context: fork
agent: planner
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /plan-work

Read-only. Produce a structured implementation plan for the request below. Do not implement anything; do not switch Plan Mode on or off — this command exists because a written plan artifact is wanted, not a mode.

## Request
$ARGUMENTS

## Procedure
1. Run the `planner` skill's Complexity Gate first (Trivial / Standard / Complex / Strategic) and state it.
2. Ground the plan in **current-state evidence**: read the relevant entry points, modules, tests, configs, and recent `git log` before writing steps. Cite `file:line` for every component you claim is affected.
3. Follow the `planner` method in order: goal, scope (In / Out / Deferred), constraints, assumptions with confidence, decomposition with done conditions, dependencies, effort (no `L` survives), risks with detection signal + mitigation, acceptance criteria, open questions, Handoff Package, 5-dimension self-check.
4. Add the two sections the guidance requires of a plan-work artifact and the planner template does not already carry:
   - **Testing** — which test types prove each phase (unit / integration / e2e / manual), and which existing tests must keep passing.
   - **Rollback** — how each mutating step is reversed (revert commit, feature flag, migration down, config restore).
5. If the request is Strategic, stop at the upstream sections and route to `/architect` (or `/ai-design` when AI is involved) before any step detail.

## Output contract
The `planner` skill's Required output format, plus `### Testing` and `### Rollback`, plus a final line:
`Next command: /architect | /ai-design | /build | /fix | /test — <reason>`

## Rules
- Never choose technologies, architecture, or cloud services — surface them as decisions for `/architect`.
- Never write production code; pseudocode only when it clarifies a step.
- Missing information goes to Open Questions, not into assumptions dressed as facts.
- Read-only: `Bash` for `git log/diff`, listing, and running existing read-only scripts only.
