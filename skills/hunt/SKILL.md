---
name: hunt
description: Read-only deep root-cause investigation of an application bug via the bug-hunter subagent — symptom, reproduction, evidence, ranked hypotheses, disproved hypotheses, root cause at High confidence, validation predictions, observability gaps, regression risk, and a fix specification. Never edits code. Use when the cause is unknown, symptoms are inconsistent, or a previous fix did not work. Use built-in /debug for Claude Code runtime issues instead.
argument-hint: "<bug description, error message, failing scenario, or log excerpt>"
disable-model-invocation: true
context: fork
agent: bug-hunter
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /hunt

Read-only root-cause investigation. You find the cause; `/fix` repairs it. Never edit code, never apply a speculative patch to "see if it helps".

## Bug report
$ARGUMENTS

## Procedure
Follow the `bug-hunter` skill end to end and the debugging sequence in `guidence/GUIDE.md` §8:

1. **Capture** observed vs expected, exact error text, onset, environment.
2. **Reproduce** — build the minimal reproduction. If you cannot, that is finding #1: investigate environment differences before hypothesizing.
3. **Collect evidence** — logs with timestamps, stack traces, state snapshots, query results, `git log`/`git bisect` around onset. Every hypothesis must explain ALL of it.
4. **Hypothesize** 2–3 ranked causes, each with a predicted observable and a discriminating check. Test the cheapest first.
5. **Narrow** by commit / input / code path until the smallest flip is found.
6. **Root cause** at `file:line` with the causal chain to the symptom. Hand off only at High confidence.
7. **Counter-evidence** for every rejected hypothesis.
8. **Validation predictions** — what disappears after the fix, what must remain unchanged.
9. **Observability gaps** and **regression risk** of the proposed fix.
10. **Fix Specification** for `developer` (consumed by `/fix`), and a one-line regression-test spec for `qa-engineer`.

## Output contract
The `bug-hunter` skill's Required output format. Confidence must be stated; if it is not High, the last section is `### Evidence still needed` — exact observations that would raise confidence — instead of a Fix Specification.

## Rules
- Correlation is not causation; a log line is not proof; a workaround is not a root cause.
- Do not stop at "add a null check" — explain why the null appeared.
- If the root cause is architectural, route to `/architect`, not to `/fix`.
- If the root cause is security-relevant, flag `security-reviewer` in the hand-off.
- Read-only: `Bash` for reproduction, `git log/bisect`, existing tests, read-only queries only.
