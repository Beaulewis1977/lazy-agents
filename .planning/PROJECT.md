# LazyAgents Frontier-Style Platform

## What This Is

LazyAgents is a self-hostable, vibecoder-focused version of an enterprise frontier-style agent platform, built for solo builders and small engineering teams. It provides one control plane to create/run agents and connect across users' tools, sites, and accounts through native integrations and upcoming MCP server support. The product goal is to make enterprise-like agent orchestration usable and installable without enterprise overhead.

## Core Value

Users can securely run and connect agents across all their tools from one place, with production-ready behavior on a self-hosted single-VM deployment.

## Requirements

### Validated

- ✓ Landing page and dashboard shell exist and are navigable — existing
- ✓ Users can create, view, update, delete, and run agents via API/UI — existing
- ✓ Agent executions are persisted with status/output and can stream logs over WebSocket — existing
- ✓ Native integrations can be listed, created, deleted, and connection-tested (GitHub/Discord/Slack/Notion/Webhook + model providers) — existing
- ✓ Integration credentials are encrypted before database storage — existing

### Active

- [ ] User can configure MCP servers (CRUD + restart + sync) and see server/tool status in UI
- [ ] Agent can invoke discovered MCP tools end-to-end via `mcp::{server}::{tool}` routing
- [ ] Native integrations and MCP flows are production-ready (stable behavior, strong error handling, clear runtime diagnostics)
- [ ] Auth is secure-by-default for non-development installs (no accidental open mode)
- [ ] Secrets are secure for real users/operators (encrypted at rest, masked in UI, never exposed in API/log payloads)
- [ ] Self-host install on Docker Compose (single VM) reaches first successful agent run quickly and predictably
- [ ] Platform acts as a unified control plane for agents + integrations in one place

### Out of Scope

- Enterprise-heavy identity/governance features (SSO/SAML, SCIM, advanced org policy engines) — explicitly deferred by user for this project scope
- Native mobile apps (iOS/Android) — explicitly deferred by user for this project scope
- Public skill/integration marketplace and monetization — not required for this v1 outcome

## Context

The project is guided by `PRD.md` and a concrete MCP expansion target in `docs/MCP_INTEGRATION_PLAN.md`. Current codebase already includes a functional split frontend/backend architecture (Next.js + FastAPI), agent CRUD/execution paths, native integration management, and execution log streaming, but MCP runtime and UI are not yet implemented. This is a brownfield continuation where existing behavior must be preserved while hardening to production-ready quality for solo and small-team self-hosting.

## Constraints

- **Deployment**: Docker Compose on a single VM — this is the mandatory v1 deployment target
- **Architecture**: Evolve in place on the existing codebase (no full re-architecture) — preserve momentum and existing behavior
- **Security**: v1 must include auth-required defaults and robust secrets handling — users will install and use this in real environments
- **Scope Discipline**: v1 includes control plane, universal connectivity, reliability, security baseline, and installability — no enterprise-heavy controls or mobile apps

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 focuses on integrations hub + universal connectivity as core workflow | User prioritized "all in one place" and interaction with all tools/sites/accounts | — Pending |
| v1 quality bar is production-ready | User explicitly set v1 as production-ready for real users | — Pending |
| Deployment target is Docker Compose on a single VM | Fastest secure self-host path for solo/small-team operators | — Pending |
| Security baseline includes auth + secrets hardening in v1 | Required for others to install/use safely | — Pending |
| Build strategy is in-place evolution of current stack | User requested no major rewrite | — Pending |
| MCP integration plan is in-scope and must be implemented | User explicitly called out `docs/MCP_INTEGRATION_PLAN.md` as required | — Pending |

---
*Last updated: 2026-02-08 after initialization*
