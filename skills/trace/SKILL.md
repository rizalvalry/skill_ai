---
name: trace
description: Read-only end-to-end trace of ONE behavior via the bug-hunter subagent — from entry point through validation, authentication/authorization, service and domain logic, persistence, external calls, error handling, and the returned result — with file:line for every hop. Use to understand a flow before changing it, to answer "what happens when X", or as the first step before /hunt or /refactor.
argument-hint: "<behavior to trace, e.g. 'POST /orders' or 'password reset email'>"
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

# /trace

Read-only. Trace exactly one behavior through the code as it IS. This is not a diagnosis (`/hunt`) and not a map (`/map`); include a Hypotheses section only if you observe a defect while tracing.

## Behavior
$ARGUMENTS

## Procedure
1. **Locate the entry point** — route/handler/command/consumer/UI event. If ambiguous, list candidates and pick the most specific; state the choice.
2. **Follow the call chain hop by hop.** For each hop record: `file:line`, what it does in one clause, what it can reject/throw, and what state it reads or writes.
3. **Cover every stage** explicitly — write `none` when a stage is absent (that is itself a finding):
   - Input validation (where, what is validated, what is not)
   - Authentication / authorization checks
   - Service / domain logic and business rules
   - Persistence (queries, transactions, isolation, side tables)
   - External calls (APIs, queues, caches, LLM/tool calls) with timeouts/retries
   - Error handling (caught where, mapped to what, logged how, swallowed?)
   - Returned result / emitted events / response shape
4. **Note the invariants** the flow depends on (ordering, uniqueness, idempotency, auth context) and where each is enforced.
5. **Flag observations** — dead code, duplicated validation, missing authz, secrets in logs, unbounded queries — as observations with evidence, not fixes.

## Output contract
```
### Behavior traced             (one sentence + chosen entry point)
### Trace                       (ordered table: # · file:line · stage · what happens · can fail with)
### Stage coverage              (validation / authn-authz / domain / persistence / external / errors / result — present or none)
### Invariants and where enforced
### Observations                (evidence-backed; no fixes)
### Hypotheses                  (ONLY if a defect was observed — otherwise omit)
### Not traced                  (branches skipped and why)
Next command: /hunt | /refactor | /build | /security — <reason>   (or "none")
```

## Rules
- One behavior only. If the request names several, trace the first and list the rest under Not traced.
- Do not redesign or fix; observations only.
- Read-only: `Bash` for `git log/blame`, listing, and read-only queries only.
