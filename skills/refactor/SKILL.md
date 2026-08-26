---
name: refactor
description: Behavior-preserving restructuring in the main session — establish observable behavior first (existing tests or characterization tests), keep public contracts stable unless explicitly asked otherwise, change in small verified steps, run the relevant tests after each, and report what moved and what was proven unchanged. Use for readability, duplication, structure, or dependency clean-up. Not for bug fixes (/fix) or features (/build).
argument-hint: "<code area to refactor and the goal (e.g. 'extract payment validation', 'remove duplication in X')>"
disable-model-invocation: true
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /refactor

Mutable work stays in the main session. A refactor changes structure, never behavior. If you cannot prove behavior is unchanged, you are not refactoring — stop.

## Request
$ARGUMENTS

## Procedure
1. **Load method** — `developer` skill (Skill tool: `skill-ai:developer`), Lane declared. Refactors touching public contracts, persistence, or auth are always `FULL`.
2. **Define the target behavior** — list the observable behaviors of the code being restructured (inputs → outputs, side effects, errors, events, performance characteristics that matter). Optionally run `/trace` first for a non-trivial flow.
3. **Establish the safety net** — locate tests that pin those behaviors. Where coverage is missing for a behavior you will move, add characterization tests FIRST (they assert current behavior, even if odd) and run them green before touching structure.
4. **Contracts stay stable** — public signatures, return shapes, error contracts, event payloads, DB schema, API responses remain identical unless the request explicitly authorizes a change — and then it is a `/build` with a compatibility plan, not a refactor.
5. **Refactor in small steps** — one mechanical move at a time (extract, inline, rename, move, replace conditional with polymorphism, remove duplication). Run the relevant tests after each step; never batch several moves between test runs.
6. **No hidden fixes or features** — a defect discovered mid-refactor goes into `Found, not changed` for `/hunt` or `/fix`; do not fix it inside the refactor. No new capabilities.
7. **Verify** — full relevant suite, type check, lint; confirm characterization tests still pass unchanged; confirm no contract drift (`git diff` of interfaces/schemas is empty or explained).
8. **Clean up** — remove dead code the refactor made unreachable (only that); keep characterization tests unless they duplicate stronger tests.

## Completion contract (guidance §15)
```
### Result                           (what was restructured, in one paragraph)
### Behaviors proven unchanged       (behavior · pinning test · run result)
### Changed files/components
### Contracts                        ("unchanged" — or the explicit authorization and compatibility note)
### Tests/checks executed and result
### Found, not changed               (defects/opportunities routed to /hunt, /fix, or /build)
### Known risks / not verified
```

## Rules
- Behavior first, structure second: no structural edit before the safety net is green.
- Smallest steps; test between steps.
- Never widen scope ("while I'm here"); never change contracts without explicit authorization.
- Never delete a test to make a refactor pass.
- Preserve existing architecture and conventions; architectural restructuring is `/architect`'s decision first.
