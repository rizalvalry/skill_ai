---
name: eval
description: Build an AI evaluation plan via the ai-engineer subagent — success criteria, dataset sources, golden cases, edge cases, adversarial and prompt-injection cases, tool-failure cases, hallucination checks, latency/cost budgets, scoring method, pass thresholds, regression policy, and the release gate. Read-only; produces the eval matrix and case specifications that developer implements and gatekeeper enforces. Use before shipping or changing any AI feature.
argument-hint: "<AI feature, prompt, agent, or RAG pipeline to evaluate>"
disable-model-invocation: true
context: fork
agent: ai-engineer
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: command
  layer: command
---

# /eval

Read-only. Design the evaluation that decides whether this AI feature may ship and keeps deciding on every change. Output is a matrix and case specs — implementation is `developer`'s (`/build`), enforcement is `/gate`'s.

## Target
$ARGUMENTS

## Procedure
1. **Read the feature as built or designed** — prompts, tools, retrieval, output schema, existing evals/tests, production logs if provided. Identify the task type (per `ai-engineer` skill) — metrics follow from it.
2. **Success criteria** — business outcome → measurable proxies. State what "correct" means and who decides for ambiguous cases.
3. **Dataset plan** — sources (production samples, synthetic, hand-written), sampling, labeling method, PII handling, size per case class, refresh cadence, ownership.
4. **Case classes** — specify concrete cases for each; minimum counts stated:
   - Golden (representative, known-good answers)
   - Edge (boundaries: empty, huge, ambiguous, multilingual, malformed)
   - Adversarial (jailbreak attempts, contradictory instructions)
   - Prompt injection (instructions embedded in retrieved docs / tool output / user content)
   - Tool failure (timeout, error, partial, wrong schema)
   - Hallucination probes (questions with no answer in sources; fabricated-entity checks)
   - Regression (every past incident becomes a case)
   - RAG-specific when applicable: retrieval recall@k / MRR on golden Q→chunk pairs; groundedness; citation correctness
5. **Scoring** — exact-match / schema-valid / rubric / LLM-judge (with judge calibration cases and human spot-check rate) / deterministic checkers. Prefer deterministic where possible.
6. **Thresholds** — per metric: release-blocking floor, warning band, target. Justify each from risk, not habit.
7. **Latency & cost** — p50/p95 budgets, tokens per request, monthly projection at expected volume; thresholds.
8. **Regression policy** — when evals run (PR, nightly, pre-deploy, model/prompt change), what blocks merge, how flaky judges are handled, how the dataset is versioned.
9. **Release gate** — the exact checklist `/gate` will read: which metrics, which thresholds, which artifacts (run ID, dataset version, model version).
10. **Observability link** — which production signals mirror the eval metrics so drift is detected after release.

## Output contract
```
### Feature & task type
### Success criteria            (outcome → metric → threshold)
### Dataset plan
### Eval matrix                 (table: case class · count · example cases · scoring method · threshold · blocks release?)
### Latency & cost budgets
### Regression policy
### Release gate checklist      (for /gate)
### Observability link          (eval metric → production signal)
### Not verified
Next command: /build (implement evals) | /gate | /prompt | /rag — <reason>
```

## Rules
- Every material prompt rule and every past incident has at least one case.
- LLM-as-judge is never the only scorer for a release-blocking metric without human calibration evidence.
- Thresholds are explicit numbers, not "high accuracy".
- Do not implement eval code; specify it.
- Read-only `Bash` (inspection, running existing eval suites) only.
