# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-08)

**Core value:** Users can securely run and connect agents across all their tools from one place, with production-ready behavior on a self-hosted single-VM deployment.
**Current focus:** Phase 3.1 - Custom Integration Types and MCP JSON Import (INSERTED)

## Current Position

Phase: 3.1 of 6 (Custom Integration Types and MCP JSON Import - INSERTED)
Plan: Not yet planned
Status: Not started
Last activity: 2026-02-08 — Phase 3.1 inserted after Phase 3 completion

Progress: [██████░░░░] 60% (phase 3.1 is urgent insertion work)

## Performance Metrics

**Velocity:**
- Total plans completed: 9
- Average duration: 14 min
- Total execution time: 2.03 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | 82 min | 27 min |
| 2 | 3 | 17 min | 6 min |
| 3 | 3 | 23 min | 8 min |

**Recent Trend:**
- Last 5 plans: 02-02 (3 min), 02-03 (9 min), 03-01 (7 min), 03-02 (6 min), 03-03 (10 min)
- Trend: Excellent consistency on focused plans

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Initialization: Keep existing stack and evolve in place
- Initialization: v1 must include MCP implementation plus production-ready security baseline
- Phase 01-01: Non-development startup now fails fast if APP_DEBUG is enabled, API_KEY is missing, or SECRET_KEY is weak/default.
- Phase 01-01: Protected APIs are fail-closed outside development when API auth is unconfigured.
- Phase 01-02: Redaction helper is centralized and applied at persistence, log emission, and API response boundaries.
- Phase 01-02: Settings UI stores only non-sensitive preferences; secrets remain transient session inputs.
- Phase 01-03: Production deployment path is explicit via `docker-compose.yml` + `compose.production.yaml` merge.
- Phase 01-03: Operator setup docs now include production env guardrails and `/health` + `/health/ready` verification steps.
- Phase 01-03: Production overlay uses compose override semantics to remove dev bind mounts and preserve only required data mounts.
- Phase 01-03: Worker service is profile-gated (`worker`) until a concrete backend worker entrypoint exists.
- Phase 02-01: Store MCP env values encrypted at rest and only expose masked env metadata via API responses.
- Phase 02-01: Enforce strict Pydantic validation for MCP args/env payload shape to keep 4xx errors actionable.
- Phase 02-02: Manage MCP runtimes via a FastAPI lifespan singleton (`app.state.mcp_manager`) for deterministic startup/shutdown ownership.
- Phase 02-02: Persist deterministic `last_error` lifecycle text and surface it through list/get/restart/sync API contracts.
- Phase 02-03: Use typed `mcpServersAPI` client methods and refresh after lifecycle actions to keep UI status authoritative.
- Phase 02-03: Keep env update payload optional in edit flows to preserve stored encrypted env values.
- Phase 03-01: Use React Hook Form + Zod for form validation instead of manual state management.
- Phase 03-01: Fetch last execution via backend query param instead of N+1 frontend queries.
- Phase 03-01: Expandable table rows for execution details instead of separate detail page.
- Phase 03-01: Replace two-step wizard with single comprehensive form.
- Phase 03-02: Custom SchemaRenderer component without external dependencies for minimal bundle size.
- Phase 03-02: Boolean() wrapper for TypeScript conditional rendering to avoid unknown type issues.
- Phase 03-02: Defensive optional chaining for tools_detected array since MCP servers return loosely-typed metadata.
- Phase 03-03: Add verify_api_key dependency override to MCP test fixtures for auth-gated routes.

### Roadmap Evolution

- Phase 3.1 inserted after Phase 3: Custom Integration Types and MCP JSON Import (URGENT)
  - Reason: Enhance integration/MCP operator UX before proceeding to runtime invocation work
  - Scope: Custom integration type catalog + MCP JSON config import flows

### Pending Todos

None yet.

### Blockers/Concerns

- MCP auth/profile variation across third-party servers may require phase-specific validation.
- Existing contract drift risks between frontend/backend require early test coverage.

## Session Continuity

Last session: 2026-02-08 20:17
Stopped at: Phase 3.1 inserted (urgent work) — not yet planned
Resume file: None — Phase 3.1 ready for planning
