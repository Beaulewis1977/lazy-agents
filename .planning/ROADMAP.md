# Roadmap: LazyAgents Frontier-Style Platform

## Overview

This roadmap delivers a production-ready, self-hosted agent control plane by extending the current brownfield system with MCP server lifecycle management, MCP tool invocation in agent runtime, and secure-by-default operational behavior. The sequence prioritizes trust and operability first, then connectivity depth, then end-to-end hardening so the platform can be installed and used safely by solo builders and small teams.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Security and Deployment Baseline** - Enforce secure defaults and establish reliable single-VM Compose deployment.
- [ ] **Phase 2: MCP Server Control Plane** - Add MCP server persistence, lifecycle operations, and status management.
- [ ] **Phase 3: Agent UX and MCP Tool Visibility** - Complete operator-facing agent workflows and MCP tool browsing.
- [ ] **Phase 4: MCP Runtime Invocation Integration** - Route namespaced MCP tools through agent execution and persist robust results.
- [ ] **Phase 5: Production Hardening and First-Run Validation** - Prove installability, persistence, and production-readiness across restart and regression flows.

## Phase Details

### Phase 1: Security and Deployment Baseline
**Goal**: Operators can run the platform on a single VM with secure defaults that protect credentials and API access.
**Depends on**: Nothing (first phase)
**Requirements**: [SEC-01, SEC-02, SEC-03, SEC-04, OPS-01]
**Success Criteria** (what must be TRUE):
  1. In non-development mode, protected API routes reject unauthenticated requests.
  2. Credential values are encrypted at rest, masked in UI, and excluded from API responses/logs.
  3. Operator can start the stack via Docker Compose and reach the dashboard/API health endpoints.
**Plans**: 3 plans

Plans:
- [ ] 01-01: Enforce fail-closed auth and startup validation for production profile
- [ ] 01-02: Standardize secret masking/redaction across API/UI/log surfaces
- [ ] 01-03: Harden and verify single-VM Compose deployment baseline

### Phase 2: MCP Server Control Plane
**Goal**: Operators can configure, run, and manage MCP servers from the platform with clear runtime status.
**Depends on**: Phase 1
**Requirements**: [MCP-01, MCP-02, MCP-03, MCP-04]
**Success Criteria** (what must be TRUE):
  1. User can create, edit, and delete MCP server configs with validated inputs.
  2. User can restart/sync servers and see status transitions (`stopped`, `starting`, `running`, `error`).
  3. When failures occur, last error details are visible and actionable to operators.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Implement MCP data model and CRUD API endpoints
- [ ] 02-02: Build manager lifecycle state machine with restart/sync operations
- [ ] 02-03: Add MCP server management UI with status and error surfaces

### Phase 3: Agent UX and MCP Tool Visibility
**Goal**: Operators can fully manage agent workflows and inspect available MCP tools before execution.
**Depends on**: Phase 2
**Requirements**: [CTRL-01, CTRL-02, CTRL-03, MCP-05]
**Success Criteria** (what must be TRUE):
  1. User can list agents with status and recent run context.
  2. User can create/update agents and manually run them through the control plane.
  3. User can browse discovered MCP tools and understand required inputs from schema details.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Improve agent list/detail UX completeness for v1 workflows
- [ ] 03-02: Add MCP tool browser and schema rendering surfaces
- [ ] 03-03: Validate UX contracts between frontend API client and backend responses

### Phase 4: MCP Runtime Invocation Integration
**Goal**: Agents can invoke MCP tools reliably using canonical namespaced identifiers, with complete execution traceability.
**Depends on**: Phase 3
**Requirements**: [MRT-01, MRT-02, MRT-03]
**Success Criteria** (what must be TRUE):
  1. Agent runtime can resolve and invoke `mcp::{server}::{tool}` IDs successfully.
  2. Successful tool calls persist structured outputs in execution steps.
  3. Failed tool calls persist actionable error details without silent failures.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Add MCP registry/executor adapters and namespace resolution
- [ ] 04-02: Integrate MCP dispatch path into skill executor runtime
- [ ] 04-03: Strengthen execution-step/log persistence for MCP success/failure paths

### Phase 5: Production Hardening and First-Run Validation
**Goal**: A new operator can install, run, and recover the platform with confidence in persistence and baseline reliability.
**Depends on**: Phase 4
**Requirements**: [OPS-02, OPS-03]
**Success Criteria** (what must be TRUE):
  1. Fresh install reaches first successful agent run via documented setup flow.
  2. Restarting services preserves agents, integrations, and MCP server configurations.
  3. Regression checks confirm MCP additions do not break existing native integration workflows.
**Plans**: 3 plans

Plans:
- [ ] 05-01: Implement first-run verification path and setup doc alignment
- [ ] 05-02: Add persistence/restart validation coverage
- [ ] 05-03: Run end-to-end regression suite for native + MCP execution paths

## Progress

**Execution Order:**
Phases execute in numeric order: 2 → 2.1 → 2.2 → 3 → 3.1 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Security and Deployment Baseline | 0/3 | Not started | - |
| 2. MCP Server Control Plane | 0/3 | Not started | - |
| 3. Agent UX and MCP Tool Visibility | 0/3 | Not started | - |
| 4. MCP Runtime Invocation Integration | 0/3 | Not started | - |
| 5. Production Hardening and First-Run Validation | 0/3 | Not started | - |
