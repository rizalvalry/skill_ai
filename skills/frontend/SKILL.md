---
name: frontend
description: Load when working on client-side UI code — components, state management, data fetching, forms, routing, accessibility, performance, or design-to-code from Figma — in any web or mobile framework (React, Vue, Angular, Svelte, Flutter, React Native). Provides implementation conventions and review checklists for UI code WITHIN an already-chosen framework and an approved design. Never makes framework, state-library, or build-tooling decisions (that is solution-architect) and never critiques the design itself (that is ui-ux). Informs developer, qa-engineer, and security-reviewer; does not replace them.
user-invocable: false
license: MIT
metadata:
  author: rizalvalry
  version: "1.0.0"
  category: reference
  layer: reference
---

# Frontend Reference v1.0

Conventions and checklists for implementing or reviewing UI code WITHIN an already-chosen framework and an approved design. This file informs; it never decides.

## Ownership boundary

| Concern | Owner | This reference... |
|---|---|---|
| Framework / state library / build tooling / rendering strategy (SSR, SSG, SPA) selection | `solution-architect` | assumes the choice is made; never proposes one |
| Design review, UX heuristics, design gaps, microcopy, Figma file hygiene | `ui-ux` | flags a gap to `ui-ux`; never redesigns |
| Writing or modifying UI code | `developer` | supplies the conventions `developer` applies |
| Implementation-vs-design verification, test scenarios, coverage gaps | `qa-engineer` | supplies what to check; never authors scenarios |
| Client-side data exposure, token storage, XSS/CSRF findings | `security-reviewer` | supplies hygiene rules; findings belong to the reviewer |

Consumed by `/build`, `/fix`, `/refactor`, `/trace`, `/security`.

## Grounding rule

- Never invent framework or library API behavior. Verify against the repository (existing usage, lockfile version), official docs, or the `documentation` MCP before relying on a hook, directive, lifecycle, or config key.
- When a Figma URL is given, use the `figma` MCP (design context, variable definitions, Code Connect map) to read tokens, spacing, and component names. Do not guess values from a screenshot.
- Match the framework version actually installed; APIs drift across majors.
- Mark anything not checked as `unverified` in the output. A guess labeled as fact is a defect.

## Component boundaries

| Type | Holds | Must not |
|---|---|---|
| Presentational | markup, styling, local UI state (open/closed, hover) | fetch data, know routes, import stores |
| Container / feature | data fetching, store wiring, route params, orchestration | contain non-trivial markup |
| Layout | grid/regions/slots | hold business state |
| Page / screen | composes containers, owns page-level effects (title, analytics) | duplicate feature logic |

- One component, one reason to change. Split when props exceed ~8 or when two unrelated states live together.
- Props are the contract: typed, required by default, no boolean explosion (`variant` enum over `isPrimary`/`isDanger`/`isGhost`).
- Reuse existing design-system components before creating new ones (repository-first).

## State placement

Escalate only when a sibling or ancestor needs the value: **local → lifted to nearest common parent → feature store → global store**.

| State kind | Lives in | Notes |
|---|---|---|
| Server state (remote data) | query/cache layer keyed by request | not copied into a global store |
| Client UI state (modals, tabs, filters) | local or URL | URL when it must survive reload/share |
| Session / auth / theme | global store or context | small, rarely-changing |
| Form state | form layer | not mirrored into global store |
| Derived state | computed at render or selector | never stored twice |

## Data fetching

- Every fetch renders **four states**: loading, empty, error, success. Stale-while-revalidate is a fifth when caching exists. Missing states are a design gap → flag to `ui-ux`; do not invent them silently.
- Cache keys include every input that changes the response (id, filters, page, locale, tenant).
- Cancel in-flight requests on unmount or param change (AbortController or the equivalent library option).
- Retries: bounded, exponential backoff, idempotent requests only. Never retry mutations blindly.
- Mutations: optimistic update only with a rollback path; invalidate or patch affected cache keys.
- Pagination or infinite scroll for unbounded lists; never load "all".
- Surface errors as typed objects (status, code, message) — not as raw strings from the network layer.

## Forms

- Validation at field level (on blur/change after first interaction) AND at submit; server errors mapped back to fields.
- Error messages are rendered adjacent to the field, associated via `aria-describedby`/`aria-invalid`, and announced (live region on submit failure).
- Disable double-submit; show pending state; keep values on failure.
- Never trust client validation as security — the server validates again.
- Prefer the one form library already in the repo; do not add a second.

## Routing

- Route guards redirect before render, preserve the intended destination, and never flash protected content.
- Route params are validated/coerced at the boundary; 404/403 states are real screens.
- Lazy-load routes at the route boundary, not per component.
- Scroll restoration and document title handled per route.

## Design tokens and layout

- Tokens (color, spacing, radius, typography, elevation, motion) over hardcoded values. New literal value → check the design system first; if genuinely missing, flag to `ui-ux`.
- Spacing and type follow the design scale; no ad-hoc `13px`.
- Responsive: mobile-first, container queries or breakpoints from the design system, no fixed pixel widths on content containers.
- Dark/light and RTL supported via tokens and logical properties when the product requires them.

## Accessibility (implementation side)

- Semantic HTML first (`button`, `nav`, `main`, `label`, headings in order); ARIA only when semantics are unavailable.
- Every interactive element is keyboard-reachable and operable; focus order follows visual order; visible focus ring.
- Focus management on route change, modal open/close (trap + return), and dynamic content (live regions).
- Images have meaningful `alt` or `alt=""`; icon-only buttons have labels.
- Contrast targets are defined by `ui-ux`; implementation uses tokens that meet them and does not override with arbitrary colors.
- Touch targets ≥ 44×44 CSS px on mobile unless the design system specifies otherwise.

## Performance

- Code-split by route; lazy-load heavy, below-the-fold, or rarely-used components.
- Memoize only with profiler evidence; premature `memo`/`useMemo` is noise.
- Images: explicit dimensions, responsive `srcset`/sizes, modern formats, lazy-load off-screen.
- Virtualize lists beyond ~100–200 rendered rows or when the profiler shows layout cost.
- Avoid layout thrash: batch DOM reads/writes, animate transform/opacity, respect `prefers-reduced-motion`.
- Watch Core Web Vitals (LCP, INP, CLS) on the critical route; reserve space for async content to avoid CLS.
- Third-party scripts load async/deferred and are audited for bundle weight.

## Error handling

- Error boundaries at route level and around isolated widgets; fallback UI offers retry or navigation.
- Log with context (route, component, user-safe correlation id); never log tokens, PII, or full request bodies.
- Unhandled promise rejections are captured and reported.

## i18n / l10n readiness

- No user-facing string literals in components; use the message layer with keys and ICU/plural support.
- Dates, numbers, currency via locale-aware formatters; never string-concatenate translated fragments.
- Layout tolerates 30–50% longer strings and RTL.

## Security hygiene

- No secrets in the bundle or env-exposed build vars; anything shipped to the client is public.
- No raw HTML injection (`innerHTML`, `dangerouslySetInnerHTML`, `v-html`) without a sanitizer and a documented reason.
- CSRF protection for cookie-authenticated mutations; `SameSite` + `HttpOnly` cookies vs `localStorage` tokens is a tradeoff (CSRF exposure vs XSS exposure) — the decision is `solution-architect`'s; implementation matches it.
- Validate and encode URL params before rendering or navigating; block `javascript:` URLs.
- Do not render server error internals (stack traces, SQL) to users.
- Findings in this area are reported to `security-reviewer`, not silently patched.

## Testing pyramid for UI

| Level | Tests | Avoid |
|---|---|---|
| Unit | pure logic: formatters, reducers, selectors, validators | rendering |
| Component | behavior via user-facing queries (role, label, text): states, interactions, a11y | implementation details, snapshot-only tests |
| Integration | container + mocked API: loading/empty/error/success paths | real network |
| E2E | critical user journeys only (login, checkout, core task) | exhaustive coverage |

Scenario design belongs to `qa-engineer`; test code belongs to `developer`.

## Design-to-code checklist

- [ ] Figma tokens read via `figma` MCP and mapped to existing code tokens; unmapped tokens listed
- [ ] Every state in the design exists (default, hover, focus, active, disabled, loading, empty, error); missing states flagged to `ui-ux` as a design gap
- [ ] Spacing values match the design scale, not eyeballed pixels
- [ ] Typography uses the type scale (size, weight, line-height) from tokens
- [ ] Existing design-system components reused; new components justified
- [ ] Responsive breakpoints match the design's frames; overflow behavior defined
- [ ] Motion specs (duration, easing, reduced-motion fallback) taken from the design or design system
- [ ] Icon set and sizes match the design system; no ad-hoc SVG duplicates
- [ ] Content strings routed through the i18n layer
- [ ] Accessibility annotations (labels, roles, focus order) implemented, not just visual parity
- [ ] Code Connect mapping updated when a new design-system component is implemented

## Review checklist

- [ ] Component boundaries respected (presentational components do not fetch or know routes)
- [ ] State lives at the lowest sufficient level; server state not duplicated in a global store
- [ ] Loading, empty, error, success states all rendered and reachable
- [ ] In-flight requests cancelled on unmount/param change
- [ ] Cache keys include every response-affecting input
- [ ] Forms validate at field and submit level with accessible error association
- [ ] Route guards do not flash protected content; 403/404 handled
- [ ] No hardcoded color/spacing/type values where a token exists
- [ ] Keyboard operability and focus management verified for new interactive elements
- [ ] Route-level code splitting present; heavy components lazy-loaded
- [ ] No `innerHTML`/dangerous HTML without sanitizer and justification
- [ ] No secrets or tokens in bundle, logs, or error output
- [ ] User-facing strings externalized for i18n
- [ ] Tests target behavior via accessible queries, not implementation details
- [ ] Framework/library APIs used were verified against installed version or docs (`unverified` items listed)

## Anti-patterns

- Fetching inside presentational components
- Mirroring server data into a global store "for convenience"
- Boolean prop explosion instead of a variant enum
- Missing empty/error states — only the happy path rendered
- Hardcoded hex colors and pixel spacing next to an existing token system
- `div`/`span` with click handlers instead of `button`/`a`
- ARIA sprinkled on elements that already have native semantics
- Wrapping everything in `memo`/`useMemo` without profiler evidence
- Rendering unbounded lists without pagination or virtualization
- Snapshot tests as the only coverage for behavior
- Adding a second form/state/fetching library when one already exists in the repo
- Fixing a design gap by inventing UI instead of flagging it to `ui-ux`
