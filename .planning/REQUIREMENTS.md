# Requirements: LazyAgents Frontier-Style Platform

**Defined:** 2026-02-08
**Core Value:** Users can securely run and connect agents across all their tools from one place, with production-ready behavior on a self-hosted single-VM deployment.

## v1 Requirements

### Control Plane

- [ ] **CTRL-01**: User can view all agents with current status, last run time, and recent execution result summary.
- [ ] **CTRL-02**: User can create and update an agent with model, system prompt, skill list, and integration assignments.
- [ ] **CTRL-03**: User can manually trigger an agent run and view completion status with final output.

### MCP Server Management

- [ ] **MCP-01**: User can create an MCP server configuration with command, args, environment variables, and enabled state.
- [ ] **MCP-02**: User can update or remove an existing MCP server configuration.
- [ ] **MCP-03**: User can restart an MCP server and run a tool re-discovery sync from UI/API.
- [ ] **MCP-04**: User can view MCP server runtime status (`stopped`, `starting`, `running`, `error`) and last error message when applicable.
- [ ] **MCP-05**: User can browse discovered tools per MCP server, including tool names, descriptions, and input schema.

### MCP Runtime Integration

- [ ] **MRT-01**: Agent runtime can resolve and invoke MCP tools using canonical namespaced IDs (`mcp::{server}::{tool}`).
- [ ] **MRT-02**: Successful MCP tool calls return structured output that is persisted in execution steps.
- [ ] **MRT-03**: Failed MCP tool calls record actionable error details in execution logs/steps.

### Security Baseline

- [x] **SEC-01**: In non-development mode, protected API routes reject unauthenticated requests by default.
- [x] **SEC-02**: Integration and MCP credentials are encrypted before database persistence.
- [x] **SEC-03**: Secret values are masked in configuration UI and excluded from API response payloads.
- [x] **SEC-04**: Execution and system logs do not expose plaintext credential values.

### Deployment and Operability

- [x] **OPS-01**: Operator can start the platform on a single VM using Docker Compose with documented environment configuration.
- [ ] **OPS-02**: Fresh install can reach first successful agent execution within the documented setup flow.
- [ ] **OPS-03**: Restarting services does not lose persisted agents, integrations, or MCP server configurations.

## v2 Requirements

### Governance and Policy

- **GOV-01**: Operator can define per-agent MCP tool allowlists/denylists.
- **GOV-02**: System maintains immutable audit log of integration/MCP config changes and tool invocations.
- **GOV-03**: Operator can define environment-specific execution safety policies (for shell/file/network tool categories).

### Product Expansion

- **EXP-01**: User can onboard integrations/MCP servers from curated presets with one-click defaults.
- **EXP-02**: User can view aggregate reliability metrics by integration/tool (latency, error rate, success rate).

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Enterprise SSO/SAML/SCIM | Explicitly deferred by project scope; too large for v1 focus |
| Native mobile apps | Explicitly deferred by project scope |
| Public marketplace/monetization | Not required to validate core control-plane value |
| Full multi-tenant org/role governance suite | Out of current target persona (solo/small-team self-host) |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CTRL-01 | Phase 3 | Pending |
| CTRL-02 | Phase 3 | Pending |
| CTRL-03 | Phase 3 | Pending |
| MCP-01 | Phase 2 | Pending |
| MCP-02 | Phase 2 | Pending |
| MCP-03 | Phase 2 | Pending |
| MCP-04 | Phase 2 | Pending |
| MCP-05 | Phase 3 | Pending |
| MRT-01 | Phase 4 | Pending |
| MRT-02 | Phase 4 | Pending |
| MRT-03 | Phase 4 | Pending |
| SEC-01 | Phase 1 | Complete |
| SEC-02 | Phase 1 | Complete |
| SEC-03 | Phase 1 | Complete |
| SEC-04 | Phase 1 | Complete |
| OPS-01 | Phase 1 | Complete |
| OPS-02 | Phase 5 | Pending |
| OPS-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-08*
*Last updated: 2026-02-08 after Phase 1 verification completion*
