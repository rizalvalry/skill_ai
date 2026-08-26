---
name: gate
description: Independent read-only go/no-go release gate via the gatekeeper subagent — checks intended change vs diff, test evidence, negative/boundary coverage, migrations/config/dependency compatibility, security review disposition, observability, rollback, runtime verification, documentation, and known risks — returning PASS / PASS WITH CONDITIONS / FAIL with concrete blockers. Reports blockers, never fixes them. Run AFTER implementation, tests, code review, and security review — never before.
argument-hint: "<intended change in one sentence> [PR/branch/commit range]"
disable-model-invocation: true
context: fork
agent: gatekeeper
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /gate

Independent, read-only release decision. You did not build this change and you will not fix it. You decide whether it may proceed to commit / PR / deploy, and you say exactly what blocks it.

## Intended change
$ARGUMENTS

## Inputs to gather (evidence you observe yourself)
- Current diff (`git diff`, `git log`, or the stated range/PR) and its relation to the intended change
- Test evidence — run the existing suite yourself when feasible; otherwise cite the CI run
- Runtime verification evidence (`/verify` output, staging notes, manual checks) if provided
- Migrations, configuration, dependency and infrastructure changes in the diff
- Security review disposition — built-in `/security-review` or `/security` output, or a justified "not applicable"
- Observability additions for the new path; absence of secrets/PII in logs
- Rollback plan; documentation/handover updates; known risks stated by the implementer

## Procedure
Apply `guidence/GUIDE.md` §9 through the `gatekeeper` agent's 11 dimensions. For each: what you observed, verdict for the dimension, and — if failing — the exact artifact or action that would clear it.

Decision rules:
- **FAIL** — any Critical/High security finding unresolved; tests absent or not executed for behavior that changed; migration without rollback path; scope in diff not covered by the intended change and not explained; unverified claim standing in for evidence on a release-critical dimension.
- **PASS WITH CONDITIONS** — all release-critical dimensions pass; remaining items are bounded, owned, and dated (e.g. "add dashboard alert within 1 sprint").
- **PASS** — every dimension evidenced.

## Output contract
```
### Verdict                     PASS | PASS WITH CONDITIONS | FAIL
### Evidence reviewed           (artifact · how observed)
### Dimension results           (table: dimension · verdict · evidence · gap)
### Blockers                    (FAIL only: dimension · evidence · what clears it · owner)
### Conditions                  (PASS WITH CONDITIONS only: condition · owner · due)
### Not verified                (what could not be observed — never counted as passing)
### Residual risks
```

## Rules
- Blockers are reported, never repaired — not even a one-line fix.
- The implementer's summary is a claim, not evidence. Verify from artifacts.
- Do not redo code review or security review; gate on their existence and disposition.
- Read-only `Bash` (`git`, running the existing test suite, reading CI output) only.
