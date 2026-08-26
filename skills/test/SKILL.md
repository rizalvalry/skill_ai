---
name: test
description: Design and/or implement the smallest useful set of tests for a behavior, driven by risk — scenario design is delegated to the read-only qa-engineer subagent (equivalence classes, boundaries, negative cases, failure modes, test-type mapping, acceptance evidence), then the tests are implemented in the main session with the developer skill and actually executed. Tests behavior, not implementation trivia. Use after /build or /fix, or to audit coverage of an existing module.
argument-hint: "<design|implement|audit> <feature, module, or behavior>"
disable-model-invocation: true
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /test

Two phases with two owners: **design** (read-only, `qa-engineer`) and **implement** (mutable, main session with the `developer` skill). Mode is the first word of the request — `design`, `implement`, or `audit`; default is `design` then `implement`.

## Request
$ARGUMENTS

## Phase A — Design (delegate)
Spawn the `qa-engineer` subagent (Agent tool, `subagent_type: qa-engineer`) with: the behavior/module, the diff or files in scope, acceptance criteria (from `/plan-work` / `/architect` / the request), the existing test locations, and any `bug-hunter` regression spec. Ask for the `qa-engineer` skill's Required output format — scenarios, edge cases, risk priority, test-type mapping, coverage gaps, Acceptance Evidence.

Skip Phase A only when a complete scenario list is already supplied in the request.

`audit` mode stops after Phase A and reports the coverage-gap analysis with recommended additions — no code.

## Phase B — Implement (main session)
1. Load the `developer` skill (Skill tool: `skill-ai:developer`). Discover the repo's test conventions (framework, fixtures, naming, factories, mocking style) — reuse them.
2. Select the smallest set of scenarios that covers the highest-priority risks; state what you deliberately did not test and why.
3. Implement tests that assert **behavior** (inputs → outputs, side effects, errors, contracts), not private structure. Prefer the lowest test level that proves the behavior (unit → integration → e2e); mock only at real boundaries.
4. Every test must fail for the right reason when the behavior is broken — sanity-check at least one by temporarily breaking the code or by reasoning through the assertion.
5. Run the new tests and the existing suite; fix flakiness at the root (no retries-as-fix).
6. Record the Acceptance Evidence mapping (scenario → test name → result) for `/gate`.

## Completion contract (guidance §15)
```
### Result                           (mode · scenarios designed · tests implemented)
### Scenario → test mapping          (scenario · priority · test file:name · result)
### Deliberately not tested          (scenario · reason)
### Changed files/components
### Tests/checks executed and result (actual commands + output summary)
### Coverage gaps remaining          (for qa-engineer / next iteration)
### Next required action             (e.g. /gate)
```

## Rules
- Test behavior, not implementation trivia; no tests that merely mirror the code.
- Never weaken an assertion or delete a failing test to get green; a red test is a finding for `/hunt` or `/fix`.
- Never claim a test ran if it did not; paste the actual run summary.
- `qa-engineer` designs, `developer` implements — do not blur the two inside one context beyond this command's handoff.
