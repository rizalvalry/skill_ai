---
name: rag-patterns
description: Load when implementing, reviewing, or debugging any retrieval-augmented generation pipeline — ingestion, parsing, normalization, chunking, metadata, embeddings, indexing, retrieval (dense/sparse/hybrid), reranking, context assembly, citation, and RAG evaluation. Supplies pipeline stage patterns, the 13-class RAG failure taxonomy, and review checklists so a bad answer is classified before it is called "hallucination". Reference only — retrieval STRATEGY (chunk size, top-k, recall targets, reranking choice) belongs to ai-engineer; the vector-store PRODUCT and hosting belong to solution-architect.
user-invocable: false
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: reference
  layer: reference
---

# RAG Patterns Reference v1.0

Stage-by-stage knowledge for building and diagnosing RAG pipelines — so failures are located at the stage that caused them, not blamed on the model.

## Ownership boundary

This skill **informs; it never decides.**

| Concern | Owner | Entry point |
|---|---|---|
| Retrieval strategy, chunking strategy, context-window budget, eval design | `ai-engineer` | `/rag`, `/ai-design`, `/eval` |
| Vector DB product + hosting topology | `solution-architect` | consumes ai-engineer's *Retrieval Requirements* doc |
| Pipeline code (ingestion jobs, retriever, assembler) | `developer` | `/build`, `/fix` |
| Authorization / data-filter leaks (tenant bleed, ACL bypass) | `security-reviewer` | `/security` |
| Azure AI Search / Foundry-specific configuration | `ai-foundry` reference skill | — |

Consumed by: `/rag`, `/ai-design`, `/eval`, `/build`, `/hunt`.

## Grounding rule

Never invent embedding model dimensions, tokenizer limits, vector DB API behavior, distance metrics, or index parameters. Verify against the repository, the provider's current documentation, or the `documentation` MCP. Anything not verified is written as **"unverified"** in the output — never as fact.

## Pipeline stages

| Stage | Good looks like | Typical defect | Health evidence |
|---|---|---|---|
| Source | Inventory of authoritative sources with owner, freshness SLA, access rules | Sources assumed present; shadow copies; no owner | Source manifest; count of docs expected vs ingested |
| Parse | Text, tables, headings, and structure preserved per format | PDF tables flattened, OCR garbage, headers/footers polluting body | Sample parse diffs vs original; parse error rate per format |
| Normalize | Consistent encoding, whitespace, unit/date formats; boilerplate removed | Over-aggressive cleanup deletes meaning; encoding mojibake | Before/after samples; character-loss check on random docs |
| Chunk | Boundaries follow semantic units (section, paragraph, table row group); size fits embedding window | Sentence split mid-table; fixed-size cuts across headings; orphan fragments | Chunk length histogram; % chunks crossing a heading |
| Metadata | Doc ID, chunk ID, source, section path, timestamp, ACL/tenant, version on every chunk | Metadata dropped at chunk step; ACL missing | Null-rate per metadata field = 0 |
| Embed | One model, one version, one dimension per index; content-hash cache | Query vs doc embedded with different models/versions; truncation silently applied | Model+version recorded per vector; truncation counter |
| Index | Deterministic upsert by chunk ID; tombstones for deletes; versioned rebuilds | Duplicates on re-ingest; deleted docs still retrievable | Index doc count = expected; stale-doc probe returns nothing |
| Retrieve | Filters applied first; top-k tuned by eval; hybrid where lexical matters | ACL filter after retrieval; top-k guessed; keyword-heavy queries miss | recall@k on golden set; filter-leak probe |
| Rerank | Separate stage, scored on query+chunk pairs, cut to final k | Rerank skipped; reranker sees truncated chunks | MRR / nDCG before vs after rerank |
| Assemble context | Ordered, deduplicated, budgeted, each chunk tagged with ID | Near-duplicates fill window; instructions inside chunks unescaped | Token budget report; duplicate ratio |
| Generate | Answer constrained to supplied context; explicit refusal path | Model answers from priors when context is empty | Groundedness score; empty-context refusal rate |
| Cite | Citation refers to chunk ID, resolvable to source span | Citation by fuzzy text match; citations to chunks not in context | Citation resolution rate = 100% |
| Evaluate | Golden set, thresholds, regression run per change | Manual spot checks only; eval set never updated | Eval report attached to release |

## Failure taxonomy

**Classify before calling anything "hallucination."** First run a **retrieval-only probe** (same query, inspect the returned chunks with no generation): if the correct chunk is absent, the failure is upstream of the model; if it is present and the answer is still wrong, the failure is in assembly, prompt, or generation.

| # | Class | Discriminating check | Remediation owner |
|---|---|---|---|
| 1 | Source missing | Is the fact in any ingested document at all? Search the source system directly | Data owner / `developer` (ingestion scope) |
| 2 | Parser loss / corruption | Diff parsed text vs original page; check tables, lists, non-Latin text | `developer` |
| 3 | Normalization error | Compare pre- and post-normalize text for the affected span | `developer` |
| 4 | Chunk boundary error | Is the answer split across two chunks or cut from its heading? | `ai-engineer` (strategy) → `developer` |
| 5 | Metadata loss | Does the retrieved chunk carry source/section/ACL/timestamp? | `developer` |
| 6 | Embedding mismatch | Same model + version + dimension for query and docs? Truncation applied? | `ai-engineer` → `developer` |
| 7 | Index / update staleness | Does the index contain the latest doc version? Deleted docs still returned? | `developer` (ingestion job) |
| 8 | Recall failure | Correct chunk exists in index but not in top-k of retrieval-only probe | `ai-engineer` (top-k, hybrid, query rewrite) |
| 9 | Ranking failure | Correct chunk in top-k but below cutoff / below distractors | `ai-engineer` (reranker, fusion weights) |
| 10 | Context assembly pollution | Duplicates, contradictory versions, or injected instructions in the window | `ai-engineer` + `security-reviewer` |
| 11 | Prompt / instruction failure | Correct context present; prompt allows priors, ignores citation rule | `ai-engineer` (`/prompt`) |
| 12 | Generation / citation failure | Correct context present; answer unfaithful or citation unresolvable | `ai-engineer` (model, constraints, eval) |
| 13 | Authorization / data-filter failure | User received a chunk their ACL forbids; filter applied post-retrieval or not at all | `security-reviewer` + `solution-architect` (design) → `developer` |

Each class needs different evidence. A fix applied to the wrong class (e.g. changing the prompt for a recall failure) will "work" by coincidence and regress later.

## Patterns

- **Hybrid retrieval (dense + BM25) with fusion** — when queries contain identifiers, codes, names, or rare terms. Shape: run both retrievers, fuse (e.g. reciprocal rank fusion), then rerank. Tradeoff: two indexes to keep in sync; fusion weights need eval evidence.
- **Reranking as a separate stage** — when top-k recall is fine but ordering is not. Shape: retrieve k' (larger), rerank on full query+chunk pairs, keep k. Tradeoff: added latency per query; reranker must see untruncated chunks.
- **Parent-child / small-to-big chunks** — when small chunks retrieve well but lack context for generation. Shape: embed small child chunks; return the parent section to the generator. Tradeoff: larger context spend; parent boundaries must be semantic.
- **Metadata filtering before vector search** — always, when tenant, date, doc type, or ACL apply. Shape: pre-filter in the retriever query, never in application code after results return. Tradeoff: index must support filtered search efficiently (verify — unverified otherwise).
- **Query rewriting / HyDE / multi-query** — only when eval shows recall gains for the actual query distribution. Shape: rewrite → retrieve per variant → union → rerank. Tradeoff: extra model calls, latency, and a new failure surface (rewrite drift).
- **Freshness via incremental re-index + tombstones** — when sources change continuously. Shape: upsert by stable chunk ID, tombstone deleted IDs, record source version. Tradeoff: needs change detection; full rebuild still required on model/chunking change.
- **Deduplication of near-identical chunks** — when sources repeat boilerplate or versions. Shape: content-hash exact dedup at ingest; similarity dedup at assembly. Tradeoff: may collapse legitimately distinct versions — keep version metadata.
- **Citation by chunk ID, not text match** — always. Shape: assembler tags each chunk `[id]`; generator cites IDs; post-processor resolves IDs to source spans and rejects unknown IDs. Tradeoff: slightly stricter prompt contract.
- **Context budget allocation** — when the window is contested. Shape: fixed budget per slot (system / retrieved / history / tool output) enforced by the assembler, with truncation policy per slot. Tradeoff: some retrieved chunks are dropped — log which.
- **Refusal on low retrieval confidence** — when wrong answers cost more than no answer. Shape: if no chunk passes a score threshold or filters return empty, answer "I don't have that in the sources" and log the miss. Tradeoff: threshold must be calibrated on eval data.
- **Embedding cache by content hash** — when re-ingestion is frequent. Shape: key = hash(model, version, normalized text). Tradeoff: cache must be invalidated on model change.
- **Document-level ACL enforced in the retriever** — always, for multi-user data. Shape: the retriever receives the caller's principal and filters at query time; the model never sees unauthorized chunks. Authorization stays outside the model. Tradeoff: ACL metadata must be complete at ingest (see class 5).

## Evaluation minimum

- Golden set: query → expected chunk IDs (not expected text). Measure **recall@k** and **MRR / nDCG** on retrieval alone; re-run on every chunking, embedding, or index change.
- Answer-level: **groundedness** (every claim supported by supplied context) and **citation correctness** (every citation resolves and supports the claim).
- Required case classes: adversarial documents containing injected instructions; empty-result queries (must refuse); stale-document queries (must return current version); cross-tenant probes (must return nothing).
- Thresholds are release gates, not dashboards. Define them in `/eval`; `/gate` reads the result.

## Review checklist

- [ ] Source inventory exists with owner and freshness expectation
- [ ] Parse output sampled per format; tables and non-Latin text verified
- [ ] Chunk boundaries respect headings/sections; length distribution inspected
- [ ] Every chunk carries doc ID, chunk ID, source, section path, timestamp, ACL/tenant, version
- [ ] Query and document embeddings use identical model, version, and dimension (verified, not assumed)
- [ ] Upserts keyed by stable chunk ID; deletes produce tombstones
- [ ] ACL / tenant / date filters applied inside the retrieval query, before ranking
- [ ] Reranker receives untruncated chunks and is evaluated separately from retrieval
- [ ] Assembler deduplicates, budgets tokens per slot, and tags chunks with IDs
- [ ] Retrieved content is treated as untrusted data; instructions inside documents are neutralized
- [ ] Generator has an explicit refusal path for empty or low-confidence retrieval
- [ ] Citations resolve to chunk IDs present in the context; unknown IDs are rejected
- [ ] Golden set with recall@k, MRR, groundedness, citation thresholds exists and runs on change
- [ ] Retrieval-only probe is available for debugging
- [ ] No embedding dimension, API behavior, or limit was written down without verification

## Anti-patterns

- Calling every wrong answer "hallucination" without a retrieval-only probe.
- Fixed-size chunking that ignores headings, tables, and lists.
- Applying ACL or tenant filters in application code after retrieval.
- Embedding queries with a different model or version than the documents.
- Re-ingesting without stable chunk IDs, producing duplicates on every run.
- Citing by fuzzy text match instead of chunk ID.
- Letting retrieved document text act as instructions to the model.
- Tuning top-k, chunk size, or fusion weights by intuition instead of eval evidence.
- Adding query rewriting or multi-query "for quality" with no measured recall gain.
- Answering from model priors when retrieval returns nothing.
- Shipping a RAG change without re-running the golden retrieval set.
- Guessing vector DB behavior or limits instead of checking documentation.
