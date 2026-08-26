---
name: prompt
description: Provider-neutral prompt audit via the ai-engineer subagent — ambiguity, conflicting instructions, missing constraints, tool misuse, prompt-injection exposure, grounding gaps, output-schema weaknesses, token waste, and testability — reported as findings with evidence. Does not rewrite the prompt unless the request explicitly asks for a rewrite. Use on system prompts, tool descriptions, few-shot sets, or prompt templates.
argument-hint: "<prompt file/path or pasted prompt> [--rewrite]"
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

# /prompt

Read-only prompt audit. Findings first. Produce a rewrite ONLY if the request contains `--rewrite` or explicitly asks for one — and then as a separate section after the findings, with every change traceable to a finding.

## Prompt under audit
$ARGUMENTS

## Procedure
1. **Locate the full prompt surface** — system prompt, developer instructions, tool descriptions/schemas, few-shot examples, templates and the variables injected into them, and where untrusted content enters (retrieved docs, tool output, user text). Read the code that assembles it; cite `file:line`.
2. **Identify the task type and the consumer** — which model(s), which output consumer (human, parser, downstream tool). Constraints follow from that, not from taste.
3. Assess each dimension; record `finding | evidence (quote / file:line) | severity | fix guidance`:
   - **Ambiguity** — instructions with more than one reasonable reading
   - **Conflicts** — contradictory or precedence-unclear rules; system vs user vs tool-output hierarchy
   - **Missing constraints** — scope, refusal behavior, length/format, language, safety, error behavior
   - **Tool misuse** — tools described inaccurately, unsafe tools not gated, mutation not flagged, missing "when NOT to use"
   - **Injection exposure** — untrusted content interpolated without delimiting/isolation; no rule that content is data
   - **Grounding** — what must be cited/tool-grounded vs may be generated; refusal when evidence is missing
   - **Output schema** — structured output specified? validated downstream? failure handling?
   - **Token waste** — redundancy, stale examples, over-long boilerplate, repeated rules; estimate savings
   - **Testability** — can each rule be checked by an eval case? which rules have none?
   - **Few-shot quality** — representative, correct, consistent with the rules, not leaking secrets/PII
4. **Testability map** — for each material rule, the eval case that would prove it (feed `/eval`).

Severity: Critical (unsafe/incorrect in normal use) · High · Medium · Low · Info.

## Output contract
```
### Prompt surface              (components, assembly point, untrusted inputs)
### Findings                    (table: # · dimension · finding · evidence · severity · fix guidance)
### Testability map             (rule → eval case)
### Estimated token impact      (current vs after fixes — rough)
### Rewrite                     (ONLY when requested — full prompt, each change annotated with finding #)
### Not verified
Next command: /eval | /agent-audit | /fix — <reason>
```

## Rules
- Provider-neutral: findings must hold regardless of vendor; note vendor-specific features only as options.
- Do not silently rewrite. Without `--rewrite`, the Rewrite section is omitted.
- Quote the prompt for evidence; never paraphrase a finding into existence.
- Read-only `Bash` (inspection) only.
