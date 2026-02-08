# Feature Research

**Domain:** Self-hosted AI agent orchestration control plane with MCP connectivity
**Researched:** 2026-02-08
**Confidence:** MEDIUM-HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Agent lifecycle management (create/edit/run/disable) | Core control-plane function | MEDIUM | Already partial in current codebase; needs hardening and polish. |
| Integration management UI/API | Users need central place to connect systems | MEDIUM | Existing native integrations provide base pattern. |
| MCP server CRUD + status | MCP is the open interoperability baseline for agent tooling | MEDIUM | Includes start/stop/restart/sync and health visibility. |
| Tool discovery and schema visibility | Operators need to understand what an MCP server exposes | MEDIUM | Should include names, descriptions, and parameter schemas. |
| Execution visibility (logs/steps/results) | Operators must debug failures quickly | MEDIUM | Existing websocket log path can be extended for MCP traces. |
| Secrets safety baseline (encrypted at rest + masked UI + no secret echo) | Non-negotiable trust requirement for shared usage | MEDIUM | Explicit user requirement for v1. |
| Secure-by-default API auth posture | Self-hosted installs cannot default to open access in production | LOW-MEDIUM | Existing optional API key mode must fail closed for production profiles. |
| Fast self-host install + first successful run | Solo/small-team adoption depends on setup speed | LOW-MEDIUM | Docker Compose path is required v1 target. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Unified tool namespace (`native + MCP`) | One control plane, one mental model for operators | MEDIUM-HIGH | Makes routing and auditability easier than fragmented tooling. |
| MCP presets for common servers | Reduces setup friction for vibecoders/teams | MEDIUM | Pre-fill command/args/env patterns safely. |
| Built-in connection validation per server/tool | Fast confidence after onboarding new tools | MEDIUM | Should report actionable diagnostics, not pass/fail only. |
| Policy-aware tool exposure by agent | Reduces accidental overreach of tool access | HIGH | Can begin with coarse policy model and evolve later. |
| Cross-tool workflow reliability diagnostics | Helps teams trust automation in production | HIGH | Surfacing retries/errors/latency by tool improves ops quality. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Enterprise SSO/SCIM suite in v1 | Common enterprise checkbox | Large scope diversion from core MCP/connectivity execution | Keep API key + secure defaults in v1; defer enterprise IAM |
| Mobile app clients in v1 | “Access anywhere” appeal | Multiplies scope without strengthening core control plane | Ship responsive web UX only |
| Marketplace/monetization now | Feels like ecosystem growth | Premature before reliability/security baseline is proven | Focus on first-party + MCP connectivity quality |
| Full autonomous multi-agent orchestration graphs | Hype appeal | High complexity and hard-to-debug failure surface | Keep deterministic single-agent runtime + clear tool calls |

## Feature Dependencies

```
Secure-by-default auth + secret safety
    └──required for──> Integration/MCP management for shared use

MCP server lifecycle
    └──required for──> Tool discovery
                       └──required for──> Agent MCP tool invocation

Execution logging/traceability
    └──required for──> Production-ready reliability/debugging

Compose install baseline
    └──required for──> Fast first-run success for target users
```

### Dependency Notes

- **MCP lifecycle before invocation:** no stable tool calls without reliable process/session management.
- **Security baseline before broad adoption:** users will not trust shared installs otherwise.
- **Traceability before scale:** once multiple integrations are active, missing visibility becomes an operational blocker.

## MVP Definition

### Launch With (v1)

- [ ] MCP server CRUD + restart/sync + status surfaces
- [ ] Tool discovery and `mcp::{server}::{tool}` execution path
- [ ] Existing agent/integration flows stabilized for production behavior
- [ ] Auth-required production mode and secure secrets handling
- [ ] Docker Compose install path that reaches first successful run quickly

### Add After Validation (v1.x)

- [ ] Policy-aware per-agent tool allowlists and stronger execution controls
- [ ] Rich MCP preset catalog and import/export configs
- [ ] Expanded observability (latency/error dashboards by integration/tool)

### Future Consideration (v2+)

- [ ] Enterprise identity/governance suite (SSO/SCIM/fine-grained org policy)
- [ ] Mobile clients
- [ ] Marketplace/economy layer

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| MCP server lifecycle management | HIGH | MEDIUM | P1 |
| MCP tool discovery + invocation | HIGH | MEDIUM-HIGH | P1 |
| Secure-by-default auth + secrets posture | HIGH | MEDIUM | P1 |
| Compose install first-run reliability | HIGH | LOW-MEDIUM | P1 |
| Preset catalog | MEDIUM | MEDIUM | P2 |
| Policy-aware tool exposure | HIGH | HIGH | P2 |
| Multi-agent orchestration graphs | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Enterprise Platforms | Open-source DIY stacks | Our Approach |
|---------|----------------------|------------------------|--------------|
| Connectivity model | Often proprietary connectors + managed governance | Fragmented wrappers/scripts | Standard MCP + native integrations under one UI/API |
| Governance baseline | Strong, but heavy/costly | Usually weak by default | Pragmatic secure-by-default baseline for self-hosted users |
| Time to first value | Varies, often enterprise-heavy | Fast to prototype, weak to operate | Compose-first install + control-plane UX |

## Sources

- `PRD.md` and `docs/MCP_INTEGRATION_PLAN.md` (project intent + explicit MCP scope)
- https://modelcontextprotocol.io/docs/learn/architecture (MCP interoperability baseline)
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview (tool-use expectations in modern agent systems)
- https://docs.langchain.com/langsmith/home (industry expectation for tracing/observability workflows)
- https://docs.docker.com/compose/ (deployment simplicity expectation for self-hosting)
- Context7 `/modelcontextprotocol/python-sdk` and `/vercel/next.js/v16.1.5` (capabilities and secure deployment patterns)

---
*Feature research for: self-hosted AI agent orchestration control plane*
*Researched: 2026-02-08*
