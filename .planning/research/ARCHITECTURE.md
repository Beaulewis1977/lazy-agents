# Architecture Research

**Domain:** Brownfield MCP integration into self-hosted AI agent control plane
**Researched:** 2026-02-08
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                         │
│  Dashboard / Agents / Integrations / MCP Server Management UI     │
└───────────────────────────────┬────────────────────────────────────┘
                                │ HTTP + WebSocket
┌───────────────────────────────▼────────────────────────────────────┐
│                        API Layer (FastAPI)                        │
│ Agents API | Integrations API | Skills API | MCP API (new)        │
└───────────────┬───────────────────────┬────────────────────────────┘
                │                       │
┌───────────────▼──────────────┐  ┌────▼─────────────────────────────┐
│ Runtime Orchestration         │  │ MCP Runtime Subsystem            │
│ AgentExecutor + SkillRouter   │  │ Manager + Registry + Dispatcher  │
└───────────────┬──────────────┘  └────┬─────────────────────────────┘
                │                       │
┌───────────────▼───────────────────────▼────────────────────────────┐
│ Persistence + Local Runtime Resources                               │
│ SQLAlchemy models (agents/integrations/mcp_servers/executions)      │
│ + encrypted credentials + managed MCP subprocess sessions            │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `backend/app/api/mcp.py` | MCP server CRUD/restart/sync/status endpoints | FastAPI router with strict Pydantic schemas |
| `backend/app/mcp/manager.py` | Process/session lifecycle and health checks | Async subprocess/session manager with bounded retries |
| `backend/app/mcp/registry.py` | Discover/cache tools and provide namespace mapping | `list_tools` ingestion + canonical `mcp::{server}::{tool}` IDs |
| `backend/app/mcp/executor.py` | Execute MCP tool calls from runtime | `call_tool` dispatch adapter returning normalized result envelope |
| `backend/app/runtime/skill_executor.py` | Route `mcp::` prefix to MCP executor | Existing registry extended with MCP branch |
| `frontend/app/integrations/mcp/*` | MCP server management UI and tool browser | Forms + status cards + schema viewer + masked env handling |

## Recommended Project Structure

```
backend/app/
├── api/
│   └── mcp.py                 # MCP routes
├── mcp/
│   ├── manager.py             # lifecycle / health / restart
│   ├── registry.py            # discovery / cache / namespacing
│   └── executor.py            # tool call adapter
├── models/
│   └── mcp_server.py          # persistence model
└── runtime/
    └── skill_executor.py      # route mcp:: prefix

frontend/app/integrations/
└── mcp/
    ├── page.tsx               # list/status/manage servers
    └── [id]/page.tsx          # tool browser + diagnostics
```

### Structure Rationale

- **Dedicated `mcp/` backend module:** isolates protocol/process complexity from generic runtime logic.
- **Thin API, thick runtime services:** consistent with existing architecture and easier testing.
- **Namespace routing in one place:** avoids duplicated tool resolution logic in UI/API/runtime.

## Architectural Patterns

### Pattern 1: Adapter Layer for Tool Invocation

**What:** Map MCP tool semantics into existing skill execution contract.
**When to use:** Any dynamic MCP tool call from agent loop.
**Trade-offs:** Slight translation overhead, major runtime consistency gain.

### Pattern 2: Supervisor-managed MCP Sessions

**What:** Central manager owns session startup, health, restart, shutdown.
**When to use:** All MCP process/session handling.
**Trade-offs:** More moving parts, but avoids orphaned processes and ad-hoc failures.

### Pattern 3: Fail-Closed Security Boundary

**What:** Auth-required API behavior in non-dev profiles + encrypted secret persistence + no secret echo.
**When to use:** Always in deployed/shared environments.
**Trade-offs:** Slight setup friction, large trust/safety improvement.

## Data Flow

### Request Flow (MCP Config + Discovery)

```
UI Save Server
    ↓
POST /api/mcp/servers
    ↓
Persist config (encrypted env)
    ↓
Manager starts session + initialize
    ↓
Registry pulls list_tools
    ↓
UI reads status/tools
```

### Runtime Tool Call Flow

```
Agent loop emits tool call: mcp::linear::create_issue
    ↓
Skill executor detects mcp:: prefix
    ↓
MCP executor resolves server+tool mapping
    ↓
Manager/session call_tool
    ↓
Normalized result -> execution step/log -> LLM loop continues
```

### Key Data Flows

1. **Discovery flow:** server lifecycle -> `initialize` -> `list_tools` cache.
2. **Execution flow:** namespaced tool ID -> MCP dispatch -> normalized execution result.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users | Single API process + bounded MCP sessions per server is acceptable |
| 100-5k users | Introduce pooled session handling, stronger backpressure, and metrics-backed autosizing |
| 5k+ users | Separate MCP control-plane worker/runtime responsibilities and externalize event bus/log fanout |

### Scaling Priorities

1. **First bottleneck:** MCP process/session churn under frequent restarts. Mitigate with lifecycle pooling + exponential backoff.
2. **Second bottleneck:** Execution observability volume. Mitigate with structured aggregation and bounded websocket buffering.

## Anti-Patterns

### Anti-Pattern 1: Monolithic Executor Growth

**What people do:** Keep adding MCP concerns directly inside `AgentExecutor`.
**Why it's wrong:** Increases coupling and regression risk in critical runtime loop.
**Do this instead:** Route MCP via dedicated module + adapter boundary.

### Anti-Pattern 2: Secret Handling in Frontend State as Source of Truth

**What people do:** Keep persistent secrets in browser storage.
**Why it's wrong:** Increases leakage/XSS blast radius.
**Do this instead:** Persist encrypted secrets server-side; UI only captures transient input.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| MCP servers (local/remote) | MCP SDK client sessions over stdio/HTTP | Follow official initialize/capability/list_tools/call_tool lifecycle |
| Native APIs (GitHub/Discord/etc.) | Existing direct integration executors | Keep as first-party path alongside MCP |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| API router ↔ MCP manager | service calls | Keep API thin; manager owns lifecycle logic |
| Runtime skill executor ↔ MCP executor | adapter call | Single branch for all `mcp::` tools |
| MCP registry ↔ persistence | DB reads/writes | Cache tool definitions; avoid stale mappings |

## Sources

- Context7 `/modelcontextprotocol/python-sdk` — initialize/list/call patterns and transport examples
- https://modelcontextprotocol.io/docs/learn/architecture — host/client/server and transport model
- https://modelcontextprotocol.io/specification/2025-03-26/architecture — security/isolation principles
- `docs/MCP_INTEGRATION_PLAN.md` — project-specific target architecture
- `.planning/codebase/ARCHITECTURE.md` — current architectural baseline
- Context7 `/fastapi/fastapi` and `/vercel/next.js/v16.1.5` — boundary and deployment guidance

---
*Architecture research for: brownfield MCP integration into LazyAgents*
*Researched: 2026-02-08*
