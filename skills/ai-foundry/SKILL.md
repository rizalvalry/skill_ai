---
name: ai-foundry
description: Load when building or reviewing LLM features on Microsoft Azure AI Foundry / Azure OpenAI — model deployments, the Foundry Agent Service, Azure AI Search as the retrieval store, prompt flow and evaluation tooling, content safety, quotas and TPM, private networking for AI endpoints, and the Azure AI SDKs. Provides conventions and review checklists WITHIN an ai-engineer strategy and a solution-architect platform decision. Never selects the model, the prompt/retrieval strategy, or the platform itself — it informs the owners of those decisions.
user-invocable: false
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: reference
  layer: reference
---

# Azure AI Foundry Reference v1.0

Conventions and checklists for LLM features that run on Azure AI Foundry / Azure OpenAI, applied after the strategy and platform decisions already exist.

## Ownership boundary

This skill **informs, never decides**.

| Decision | Owner | Reached via |
|---|---|---|
| Model selection; context, retrieval, prompt, eval, memory, agent-state STRATEGY | `ai-engineer` | `/ai-design`, `/rag`, `/prompt`, `/eval`, `/agent-audit` |
| Platform, hosting, region, vector-store PRODUCT, network topology, cost tradeoffs | `solution-architect` | `/architect` |
| Integration and SDK code | `developer` | `/build`, `/fix` |
| Prompt-injection, data-leak, credential-exposure findings | `security-reviewer` | `/security` |
| General Azure identity / network / IaC conventions | `azure` reference skill | auto-loaded |
| RAG pipeline patterns (chunking, embedding, reranking, failure taxonomy) | `rag-patterns` reference skill | auto-loaded |

Consumed by: `/ai-design`, `/rag`, `/eval`, `/agent-audit`, `/build`, `/devops`. If a convention below conflicts with an explicit decision from an owner, the owner's decision wins — flag the conflict, do not override it.

## Grounding rule (critical)

The Foundry product surface changes frequently: model catalog and per-region availability, API versions, SDK package names and namespaces, quota units, portal feature names, Agent Service capabilities, and content-safety options.

- **Never assert any of these from memory.** Verify against the repository (SDK lockfiles, config, IaC), the portal or CLI output, or the `documentation` MCP (Microsoft Learn) — and cite what was checked.
- Anything not verified is written as **"unverified"** in the output. An unverified model name, API version, or package is a blocker for `/build`, not a detail to fix later.
- Prefer copying exact identifiers (deployment name, API version, package version) from repo/portal output over paraphrasing them.

## Conventions

### Deployment hygiene
- Pin the model **version** explicitly per deployment. No auto-upgrade policy in production unless an eval gate runs on the new version first.
- One deployment per environment (dev / test / prod) — never share a prod deployment with experiments.
- Size capacity (TPM / PTU) from **measured** load plus headroom; record the measurement source next to the number.
- Handle `429` with exponential backoff + jitter and a bounded retry budget; surface persistent throttling as an alert, not a silent retry loop.
- Provisioned vs pay-as-you-go is a cost/availability tradeoff owned by `solution-architect`; this skill only requires that the choice be recorded with its utilization assumption.
- Deployment name, model, version, and region are configuration, not code constants.

### Identity and network
- Authenticate to Azure OpenAI / Foundry / AI Search with **Managed Identity or Entra ID** (RBAC data-plane roles). API keys only when a dependency cannot use Entra, and then stored in Key Vault, rotated, never in client apps or notebooks.
- Production AI and Search resources sit behind **private endpoints**; public network access disabled unless an explicit, recorded exception exists.
- Least-privilege role assignments scoped to the specific resource, not the subscription.
- Keys, endpoints, and connection strings never appear in prompts, logs, evaluation datasets, or committed config.

### Retrieval on Azure AI Search
- The index schema implements `ai-engineer`'s **Retrieval Requirements** document: fields, filterable/facetable metadata, vector dimensions matching the embedding deployment, and the hybrid (vector + keyword) posture. Semantic ranker is one reranking option — its use is a strategy decision, not a default.
- **Document-level security filters are enforced by the application** (filter expression built from the caller's authorization), never inferred by the model.
- Indexer / skillset cadence must satisfy the stated freshness window; staleness is measured, not assumed.
- Chunk metadata (source, section, version, ACL tags, timestamp) is carried into the index so citations and filters work.
- The embedding deployment used at index time must match the one used at query time; changing it means re-indexing, tracked as a migration.

### Agent Service and tool use
- Tool schemas are explicit, minimal, and versioned in the repo. Descriptions state preconditions and side effects.
- Every state-mutating tool requires **app-side authorization** and **idempotency**; the agent's choice to call a tool is never the authorization decision.
- Tool outputs, retrieved documents, and user uploads are **untrusted data** — never treated as instructions.
- Enforce max-step, max-token, and wall-clock budgets per run; terminate loops explicitly and log the termination reason.
- Thread / run state is persisted and inspectable for debugging and audit; do not rely on the portal as the only view.

### Safety
- Content-safety filters configured **per deployment and per use case**; document the severity thresholds and why.
- Enable prompt-shield / jailbreak and indirect-injection detection where available for any flow that ingests external content.
- Blocklists / allowlists live as data (config or store), not inside prose prompts.
- Define PII handling (redaction, retention, residency) **before** enabling any logging of prompts or completions.

### Evaluation
- Evaluations implement `ai-engineer`'s eval matrix: task-specific golden cases plus groundedness / relevance / coherence style metrics, adversarial and injection cases, and tool-failure cases.
- Use Foundry evaluation tooling or code-based evals — either way, results are reproducible from the repo.
- An **eval gate runs in CI before any deployment swap** (new model version, prompt version, or index change). Thresholds come from the eval matrix, not from the run.
- Record eval run IDs alongside the deployment/prompt version they approved.

### Observability and cost
- Emit per request: prompt/completion tokens, latency p50/p95, error class, retrieval hit rate and top-k scores, safety-filter trigger, tool calls and their outcomes.
- Trace spans across retrieval → context assembly → generation → tool execution, correlated by request ID.
- Compute cost per request and a monthly projection from measured volume; alert on quota exhaustion and cost anomalies.
- Logs are sanitized before emission (no keys, no raw PII, no full documents unless retention policy allows).

### Prompt and asset management
- Prompts, tool schemas, and evaluation datasets are **versioned in the repository**; the portal is an experimentation surface, not the source of truth.
- Portal experiments are promoted only through code review, with the eval results attached.
- Prompt version is emitted with every request trace so quality regressions can be attributed.

## Review checklist

- [ ] Model name, version, API version, and SDK packages verified against repo/portal/docs — nothing asserted from memory.
- [ ] Each deployment pins a model version; production has no unreviewed auto-upgrade path.
- [ ] Separate deployments per environment; capacity sized from measured load with recorded headroom.
- [ ] `429` handling uses bounded backoff with jitter and alerts on sustained throttling.
- [ ] Endpoints use Managed Identity / Entra ID; any residual API key lives in Key Vault with rotation.
- [ ] Production AI and Search resources use private endpoints; public-access exceptions are documented.
- [ ] Search index schema traces to the Retrieval Requirements document; embedding deployment matches at index and query time.
- [ ] Document-level authorization filters are built by the application, not by the model.
- [ ] Every mutating tool has app-side authorization and idempotency; run budgets (steps, tokens, time) enforced.
- [ ] Tool outputs and retrieved content are treated as untrusted data in prompts and code.
- [ ] Content-safety thresholds and injection detection configured per use case and documented.
- [ ] PII handling defined before prompt/completion logging is enabled; logs sanitized.
- [ ] Eval gate exists in CI and blocks deployment swaps below threshold; eval run IDs recorded.
- [ ] Token, latency, error, retrieval, safety, and cost telemetry emitted with request correlation.
- [ ] Prompts, tool schemas, and eval datasets versioned in the repo with prompt version in traces.

## Anti-patterns

- Asserting a model's regional availability, API version, or package name from memory instead of verifying.
- Sharing one deployment between production traffic and experiments.
- Auto-upgrading the model version in production with no eval gate.
- API keys in client apps, notebooks, or committed config "temporarily".
- Letting the model decide document access instead of applying an application-built security filter.
- Changing the embedding deployment without re-indexing and treating it as a config tweak.
- Treating retrieved documents or tool results as trusted instructions.
- Agent tools that mutate state with no app-side authorization or idempotency key.
- Unbounded agent loops with no step, token, or time budget.
- Prompts edited only in the portal, with the repo lagging behind.
- Logging raw prompts and completions before defining PII redaction and retention.
- Declaring quality "good" from a demo instead of an eval run against the matrix.
