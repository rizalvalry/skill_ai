---
name: backend
description: Load when working on server-side code in any stack — HTTP/gRPC APIs, services, domain logic, persistence access, auth middleware, background jobs, queues, caching, error handling, and observability. Provides stack-agnostic conventions, review checklists, and anti-patterns for implementing or reviewing backend code WITHIN an already-chosen stack. It informs, never decides — technology, architecture, integration, scalability, and security DESIGN belong to `solution-architect`. Consumed by /build, /fix, /refactor, /trace, /security, /map.
user-invocable: false
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: reference
  layer: reference
---

# Backend Reference v1.0

Conventions and checklists for implementing or reviewing server-side code WITHIN an already-chosen stack. Framework-neutral: examples in parentheses (Express / FastAPI / Spring / .NET / Laravel / Go) illustrate, never prescribe.

## Ownership boundary

This skill **informs, never decides**.

| Concern | Owner |
|---|---|
| Technology, architecture pattern, integration, scalability, security DESIGN | `solution-architect` |
| Writing / modifying code per these conventions | `developer` |
| Vulnerability findings with evidence | `security-reviewer` |
| Test scenarios, edge cases, acceptance evidence | `qa-engineer` |
| Unknown root cause | `bug-hunter` |

Consumed by commands `/build`, `/fix`, `/refactor`, `/trace`, `/security`, `/map`. If applying a convention here would require a decision in an owned domain (new library, new broker, new auth model), stop and hand off — do not pick.

## Grounding rule

Never invent API, framework, or library behavior. Verify against (1) the repository (existing usage, lockfile versions, tests), (2) official docs for the pinned version, or (3) the `documentation` MCP (Context7 / Microsoft Learn) when connected. Anything not checked is labeled **unverified** in output. Match the repo's existing conventions before these defaults.

## Request lifecycle

Order is fixed; each stage does one job:

```
transport → parse/validate (boundary) → authn → authz → domain logic → persistence → response mapping
```

- Validate once, at the system boundary (request body, headers, path/query, webhook payload). Internal functions trust typed inputs — no redundant re-validation.
- Authn (who) precedes authz (allowed?). Authz is enforced server-side per resource, never inferred from client-supplied role fields.
- Domain logic is framework-free and unit-testable; transport types do not leak into it.
- Persistence is behind a repository/DAO boundary; the handler never composes raw queries.
- Response mapping is explicit (DTO/serializer) — never return ORM entities or internal error objects directly.

## Error contract

| Rule | Detail |
|---|---|
| Typed errors | Domain errors are named types/classes, not string matching. |
| No swallowing | Every `catch` either handles, rethrows with context, or maps to a response. Empty catch is a defect. |
| Status mapping | One central mapper: validation → 400/422, authn → 401, authz → 403, not found → 404, conflict/idempotency → 409, upstream → 502/503/504, unknown → 500. |
| Client body | Stable shape (`code`, `message`, `correlationId`, optional `details`). Never stack traces, SQL, file paths, or internal hostnames. |
| Logging | Log unknown errors once, at the boundary, with correlation ID. Do not log-and-rethrow at every layer. |

## Mutating endpoints

- **Idempotency** — POST/PUT/PATCH/DELETE that may be retried (clients, queues, webhooks) accept an idempotency key or derive a natural one; duplicates return the original result, not a second side effect.
- **Transactions** — one unit of work per request; boundary at the service layer, not inside repositories. No network I/O (HTTP, email, queue publish) inside an open transaction — use outbox / post-commit hooks.
- **Consistency** — state the guarantee (strong within the aggregate, eventual across services). Optimistic concurrency (version column / ETag) for concurrent edits; pessimistic locks only with a documented reason and timeout.
- **Concurrency hazards** — check-then-act sequences are races unless guarded by a constraint, lock, or atomic operation in the store.

## Data access

- **N+1** — any loop that issues a query is a defect; batch, join, or eager-load with explicit inclusion lists.
- **Unbounded loads** — every list query has a `LIMIT`; every collection endpoint paginates (cursor preferred over offset for large/changing sets). Max page size is enforced server-side.
- **Projections** — select the columns needed; never `SELECT *` into hot paths.
- **Indexes** — a new filter/sort in a query implies checking index coverage; note it in the change impact.
- **Migrations** — additive first (add column nullable → backfill → enforce), reversible, never coupled to a deploy that requires them to run first unless documented.

## Outbound calls (HTTP, gRPC, DB, cache, queue)

| Control | Default |
|---|---|
| Timeout | Always set connect + read timeouts; no infinite waits. |
| Retry | Only for idempotent operations and transient errors (timeouts, 429, 502–504). Bounded attempts. |
| Backoff | Exponential with jitter; honor `Retry-After`. |
| Circuit breaker | For dependencies whose failure is contagious; fail fast with a defined fallback or explicit error. |
| Bulkhead | Bounded connection/thread pools per dependency so one slow upstream cannot starve the service. |
| Propagation | Forward correlation ID / trace context on every outbound request. |

## Background jobs & queues

- Assume **at-least-once** delivery; handlers are idempotent (dedupe on message ID or business key).
- Bounded retries with backoff → **dead-letter queue**; DLQ has an owner and an alert.
- Poison messages are quarantined, not retried forever.
- Job payloads carry IDs, not fat snapshots; the handler reloads current state.
- Long jobs checkpoint progress and honor cancellation/shutdown signals.
- Schedulers are single-instance or lease-guarded to avoid duplicate runs across replicas.

## Caching

- Key design: `namespace:version:entity:id[:variant]` — include every input that changes the value (tenant, locale, permissions).
- Every entry has a TTL; "forever" is a defect.
- Invalidation strategy is written down (TTL-only, write-through, explicit purge on mutation).
- Stampede protection for hot keys (lock / single-flight / early refresh).
- Never cache per-user authorization results across users; never cache error responses without a short TTL.
- Cache misses must degrade gracefully — the cache is an optimization, not a source of truth.

## Configuration & secrets

- Config comes from environment / secret store / config service; source contains only non-secret defaults.
- Fail fast at startup on missing required config; validate types and ranges.
- Secrets are never logged, echoed in errors, committed, or embedded in connection strings that reach logs or API responses.
- Runtime-tunable operational parameters (thresholds, intervals) may live in a settings store with a TTL cache; document precedence (`code default < env < store`).

## Observability

- **Structured logs** (JSON or key=value) with level, timestamp, service, correlation ID, and event name. No free-text-only logs in hot paths.
- **Credential masking** at the logger (filter/formatter) for tokens, passwords, `user:pass@` in URLs, API keys, PII fields. Applies to messages, arguments, and exception text.
- **Correlation ID** accepted from inbound header or generated; attached to every log line and outbound call.
- **Metrics** — RED per endpoint/consumer (rate, errors, duration) plus dependency latency and queue depth/lag.
- **Traces** — one span per inbound request, one per outbound dependency; do not put payload bodies in span attributes.
- **Stage tagging** in multi-stage pipelines (`stop_stage`) so failures are queryable, not grep-able.

## Lifecycle

- `/health` (liveness: process alive) is separate from `/ready` (readiness: dependencies reachable, migrations applied). Readiness flips false during shutdown.
- Graceful shutdown: stop accepting, drain in-flight requests/jobs within a deadline, close pools, exit. Deadline is shorter than the orchestrator's kill timeout.

## API evolution (backward compatibility)

- Additive changes only on a live contract: new optional fields, new endpoints, new enum values only where clients tolerate unknowns.
- Never rename/remove fields, change types, tighten validation, or change error codes without a version bump and deprecation window.
- Version at the boundary (path, header, or media type — follow the repo's existing choice).
- Deprecations are announced in the response (header or doc), dated, and tracked to removal.
- Consumers of events: producers add fields; consumers ignore unknowns and never break on extra data.

## Review checklist

- [ ] Input validated once at the boundary; no redundant internal validation, no missing boundary validation.
- [ ] Authn then authz enforced server-side for every route/handler that needs it.
- [ ] Errors are typed, mapped centrally, never swallowed; client body leaks nothing internal.
- [ ] Mutating endpoints reachable via retry are idempotent.
- [ ] Transaction boundary is at the service layer; no network I/O inside it.
- [ ] No N+1; all list queries bounded and paginated; projections explicit.
- [ ] Every outbound call has timeouts; retries only for idempotent + transient cases, with backoff.
- [ ] Queue/job handlers idempotent; DLQ and bounded retries present.
- [ ] Cache keys include all value-affecting inputs; TTL set; invalidation documented.
- [ ] No secrets in source, logs, error messages, or serialized responses; masking filter in place.
- [ ] Logs structured with correlation ID; metrics/traces cover new endpoints and dependencies.
- [ ] Readiness reflects dependencies; shutdown drains.
- [ ] Contract change is additive or versioned with a deprecation path.
- [ ] Migration is reversible and safe to run before the new code is live.
- [ ] Existing repo conventions (naming, error handling, module layout) were matched, not replaced.

## Anti-patterns

- Fat controllers: transport handler contains business rules and raw queries.
- Boolean/`null` return for failures instead of typed errors.
- `catch (e) {}` or `catch → log → continue` hiding a broken invariant.
- Retrying non-idempotent writes "to be safe".
- Sending email / publishing events inside an open DB transaction.
- `SELECT *` + in-memory filtering instead of a bounded, indexed query.
- Client-supplied `role`, `tenantId`, or `userId` trusted for authorization.
- Connection strings with embedded credentials printed in startup logs or error text.
- Global mutable state / singletons holding per-request data.
- Sleep-based waits or unbounded polling instead of timeouts and backoff.
- Config or feature flags hardcoded, requiring a redeploy to tune.
- Breaking a live API contract (rename/remove field) in a "minor" change.
