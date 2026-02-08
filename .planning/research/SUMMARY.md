# Project Research Summary

**Project:** LazyAgents Frontier-Style Platform
**Domain:** Self-hosted AI agent orchestration control plane (brownfield MCP expansion)
**Researched:** 2026-02-08
**Confidence:** HIGH

## Executive Summary

This project is best treated as a brownfield control-plane hardening + MCP expansion effort, not a greenfield rebuild. The existing Next.js + FastAPI architecture already covers core agent lifecycle, native integrations, and execution logging, so the highest-leverage path is to add MCP runtime capabilities (server lifecycle, discovery, dispatch) while tightening production security defaults and operational reliability.

Current ecosystem signals and official MCP documentation support this direction: MCP is a host/client/server protocol with explicit initialize/capability/list/call lifecycles, and the official Python SDK provides stable stdio and streamable HTTP patterns that align directly with your existing Python backend. This allows standards-based connectivity without introducing a new orchestration framework or service topology for v1.

Primary risks are not feature ideation risks; they are operational and security execution risks: auth fail-open behavior, secret leakage across UI/API/log channels, process lifecycle instability, and tool namespace/schema drift. The roadmap should therefore front-load security and lifecycle foundations before broad MCP UX expansion.

## Key Findings

### Recommended Stack

The current stack should be retained and tightened rather than replaced: Next.js 16.1.6 + React 19.2.4 for UI, FastAPI 0.128.4 + SQLAlchemy 2.0.46 + Pydantic 2.12.5 for backend/API/data contracts, and MCP Python SDK 1.26.0 for MCP transport/session primitives.

**Core technologies:**
- **Next.js 16.1.6**: frontend control plane and secure env/CSP handling
- **FastAPI 0.128.4**: API boundary and runtime service orchestration
- **MCP SDK 1.26.0**: standards-based MCP initialize/discovery/call flows

### Expected Features

v1 should prioritize production-ready unified control-plane outcomes, not breadth. Required outcomes are MCP lifecycle + discovery + invocation, secure-by-default auth and secret handling, stable execution visibility, and fast self-host install/first run.

**Must have (table stakes):**
- MCP server CRUD/status + sync/restart
- Namespaced tool discovery and execution (`mcp::{server}::{tool}`)
- Production-safe auth defaults and secret hygiene
- Compose-first installability and reliable first execution

**Should have (competitive):**
- Unified native+MCP tool namespace and UX
- MCP presets and actionable diagnostics

**Defer (v2+):**
- Enterprise SSO/SCIM/governance suite
- Mobile clients
- Marketplace/economy layer

### Architecture Approach

Recommended architecture is a dedicated MCP subsystem inside the existing backend: `api/mcp.py` + `mcp/{manager,registry,executor}.py`, with runtime routing from `skill_executor` for `mcp::` tools. Keep API thin, runtime services explicit, and canonical tool namespacing enforced.

**Major components:**
1. **MCP Manager** — process/session lifecycle and health model
2. **MCP Registry** — discovery cache and canonical tool ID mapping
3. **MCP Executor Adapter** — normalized tool dispatch from agent runtime

### Critical Pitfalls

1. **Auth fail-open in deployment** — enforce fail-closed startup checks in non-dev profiles
2. **Secret leakage** — keep secrets server-side encrypted, masked, and redacted from logs/responses
3. **MCP lifecycle instability** — centralize subprocess/session management with bounded retries
4. **Tool namespace/schema drift** — use canonical IDs and controlled sync/cache invalidation
5. **Frontend/backend contract drift** — add contract tests for API shape stability

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Security and Deployment Baseline
**Rationale:** All shared-user value depends on trustworthy default posture.
**Delivers:** Fail-closed auth behavior, secret handling guarantees, and production profile checks.
**Addresses:** Secure-by-default and secrets baseline table stakes.
**Avoids:** Auth bypass and credential leakage pitfalls.

### Phase 2: MCP Data Model and API Surface
**Rationale:** Runtime work needs stable persisted server configs and CRUD contract first.
**Delivers:** `mcp_servers` model, MCP API endpoints, config validation.
**Uses:** Existing FastAPI + SQLAlchemy patterns.
**Implements:** MCP API boundary and persistence layer.

### Phase 3: MCP Runtime Core (Manager/Registry/Executor)
**Rationale:** Lifecycle/discovery correctness is prerequisite for trustworthy tool calls.
**Delivers:** Session lifecycle state machine, `initialize` + `list_tools` + `call_tool` flows, namespace mapping.
**Addresses:** MCP lifecycle and namespace drift pitfalls.

### Phase 4: Agent Runtime Integration
**Rationale:** MCP must function in the real execution loop, not as standalone API demos.
**Delivers:** `mcp::` routing from skill executor, normalized step logging and error handling.
**Addresses:** End-to-end invocation requirement and production reliability goals.

### Phase 5: MCP UI and Operator Workflow
**Rationale:** Control-plane promise requires operational visibility and manageable UX.
**Delivers:** MCP server management UI, status indicators, tool browser, restart/sync actions.
**Addresses:** Single-place operations and install-to-value experience.

### Phase 6: Hardening and Verification
**Rationale:** v1 target is production-ready, so release quality must be proven.
**Delivers:** Contract tests, lifecycle failure tests, install verification, regression checks against existing native integrations.
**Addresses:** Drift and reliability pitfalls before release.

### Phase Ordering Rationale

- Security and persistence precede runtime complexity to prevent costly rewrites.
- Runtime lifecycle/discovery must stabilize before UX layering.
- Integration and verification are split to isolate correctness from presentation.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Remote MCP auth patterns vary by server type and may need targeted protocol/provider validation.
- **Phase 6:** Hardening scope depends on expected concurrency and operator environment variability.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Well-documented auth/secret practices in FastAPI + deployment stacks.
- **Phase 2:** Conventional CRUD/persistence design in existing codebase.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified via Context7 + package registries and official docs |
| Features | MEDIUM-HIGH | Strong project-context evidence; market differentiation details are partly inferred |
| Architecture | HIGH | Directly aligned with official MCP architecture + existing codebase shape |
| Pitfalls | HIGH | Backed by observed codebase concerns + protocol/runtime constraints |

**Overall confidence:** HIGH

### Gaps to Address

- **MCP server heterogeneity:** Different servers expose different auth/runtime assumptions; plan phase should validate target presets explicitly.
- **Production scale envelope:** Exact throughput/concurrency expectations are not yet quantified; hardening tests should set explicit SLO targets.

## Sources

### Primary (HIGH confidence)
- Context7 `/modelcontextprotocol/python-sdk` — lifecycle/discovery/call semantics
- Context7 `/fastapi/fastapi` — auth/security dependency patterns
- Context7 `/vercel/next.js/v16.1.5` — env and CSP deployment practices
- https://modelcontextprotocol.io/docs/learn/architecture — MCP architecture
- https://modelcontextprotocol.io/specification/2025-03-26/architecture — protocol principles
- https://nextjs.org/docs/app/guides/environment-variables — env handling
- https://nextjs.org/docs/app/guides/content-security-policy — CSP patterns
- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ — auth implementation pattern
- https://docs.docker.com/compose/ — deployment target guidance

### Secondary (MEDIUM confidence)
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview — tool-use pattern expectations
- https://docs.langchain.com/langsmith/home — observability/tracing expectations
- `.planning/codebase/*.md`, `PRD.md`, `docs/MCP_INTEGRATION_PLAN.md` — project-specific baseline and intended scope

### Tertiary (LOW confidence)
- Perplexity ecosystem scans (used for directional trend discovery; not used for authoritative version claims)

---
*Research completed: 2026-02-08*
*Ready for roadmap: yes*
