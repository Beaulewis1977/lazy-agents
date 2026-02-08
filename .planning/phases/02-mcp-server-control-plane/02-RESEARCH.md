# Phase 2: MCP Server Control Plane - Research

**Researched:** 2026-02-08
**Domain:** MCP server lifecycle control plane (FastAPI + SQLAlchemy async + Next.js UI)
**Confidence:** HIGH

## Summary

Phase 2 should implement a backend-first MCP control plane using the **official MCP Python SDK client/session flow** over stdio, integrated with the existing FastAPI lifespan-managed runtime and SQLAlchemy async persistence patterns already used in this codebase.

The standard approach is: persist MCP server configs in DB, maintain an in-memory runtime manager keyed by server ID, initialize MCP sessions on demand/startup, and expose operational endpoints for CRUD + restart + sync + status/error reads. UI should consume these APIs with explicit status transitions and actionable error surfaces.

The key architecture decision is to **not hand-roll JSON-RPC transport/session handling**. Use MCP SDK primitives (`stdio_client`, `ClientSession`, `initialize`, `list_tools`, `call_tool`) and focus custom logic on lifecycle orchestration, state transitions, and operator UX.

**Primary recommendation:** Build a `backend/app/mcp/` module centered on `MCPServerManager` + persistent `MCPServer` model + dedicated `/api/mcp/servers` endpoints, then wire frontend management views to those APIs.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| MCP Python SDK (`mcp`) | latest stable (pin during implementation) | MCP stdio transport + session lifecycle + tools discovery/calls | Official protocol SDK; avoids protocol drift and hand-rolled framing |
| FastAPI | `>=0.109.0` (project baseline) | Control-plane API surface + app lifespan runtime startup/shutdown | Existing project framework; lifespan model is recommended for startup/shutdown |
| SQLAlchemy Async ORM | `>=2.0.0` (project baseline) | Persist MCP server configs/status/error/tool cache | Existing project persistence layer; async transaction patterns are well-defined |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic v2 | `>=2.5.0` (project baseline) | Request/response schemas and validation for MCP endpoints | API contracts and strict config validation |
| `tenacity` | `>=8.2.0` (already in project) | Retry policy for startup/sync operations on transient failures | Restart/sync resilience and bounded retries |
| React + Next.js API client module | Next `16.1.6`, React `19.2.3` (project baseline) | MCP management UI and status/error rendering | Existing frontend app shell and API patterns |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MCP SDK session/transport | Custom JSON-RPC over subprocess stdio | High implementation risk; protocol compatibility burden |
| In-process runtime manager | Separate worker/service | Better isolation but unnecessary complexity for current single-VM scope |
| Dynamic tool-only storage | No persistent tool cache | Simpler model but weaker operator visibility and slower UI |

**Installation:**
```bash
# backend additions for phase implementation (pin exact versions during execution)
pip install mcp
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── mcp/
│   ├── manager.py      # Lifecycle/state transitions and runtime registry
│   ├── client.py       # MCP session helpers (initialize/list_tools/call_tool)
│   └── schemas.py      # Internal MCP DTOs/state enums
├── models/
│   └── mcp_server.py   # SQLAlchemy model for persisted configs/state
└── api/
    └── mcp.py          # CRUD + restart/sync/status endpoints
```

### Pattern 1: Lifespan-managed singleton runtime manager
**What:** Initialize a single `MCPServerManager` in FastAPI lifespan and tear it down on shutdown.
**When to use:** Any long-lived process/session manager tied to app lifecycle.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mcp_manager = MCPServerManager()
    await app.state.mcp_manager.start_enabled_servers()
    yield
    await app.state.mcp_manager.shutdown_all()

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: MCP stdio session wrapper per managed server
**What:** Wrap `stdio_client` + `ClientSession` in a manager-owned runtime object.
**When to use:** Starting/restarting/syncing individual MCP server processes.
**Example:**
```python
# Source: https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession

async with stdio_client(StdioServerParameters(command=cmd, args=args, env=env)) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

### Pattern 3: Transactional status transitions in API handlers
**What:** Persist status transitions (`stopped` -> `starting` -> `running`/`error`) using `AsyncSession` transaction boundaries.
**When to use:** restart/sync/state-changing endpoints.
**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
async with session.begin():
    server.status = "starting"
    server.last_error = None
```

### Anti-Patterns to Avoid
- **Hand-rolled MCP protocol framing:** use SDK session APIs instead.
- **Global mutable runtime without lifecycle ownership:** attach manager to `app.state` and control in lifespan.
- **Opaque errors:** always persist and return actionable `last_error` details.
- **State updates outside transaction scope:** can cause stale/inconsistent operator status views.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol transport/session | Custom JSON-RPC subprocess protocol layer | MCP Python SDK `stdio_client` + `ClientSession` | Protocol correctness + lower maintenance |
| App startup/shutdown hooks | Ad-hoc globals + mixed startup/shutdown events | FastAPI `lifespan` async context manager | Predictable init/cleanup semantics |
| Retry loops for transient process failures | Manual retry/sleep spaghetti | `tenacity` with bounded retries/backoff | Fewer edge-case bugs and clearer policy |

**Key insight:** The phase value is lifecycle orchestration and operator UX, not low-level protocol implementation.

## Common Pitfalls

### Pitfall 1: Startup/shutdown mismatch with lifespan
**What goes wrong:** Legacy startup/shutdown hooks are mixed with lifespan, causing expected hooks not to run.
**Why it happens:** FastAPI uses lifespan as an exclusive lifecycle mechanism.
**How to avoid:** Put MCP manager init/cleanup entirely in lifespan.
**Warning signs:** Manager not initialized in requests, orphaned subprocesses on shutdown.

### Pitfall 2: In-memory runtime and DB status drift
**What goes wrong:** Runtime process is down but DB still says `running`.
**Why it happens:** State transitions are not centralized/atomic.
**How to avoid:** Single manager method owns transition + DB update path for restart/sync/failure.
**Warning signs:** UI status inconsistent after errors/restarts.

### Pitfall 3: Tool cache not synced after restart/config edit
**What goes wrong:** UI shows stale tool metadata.
**Why it happens:** `tools/list` not refreshed on lifecycle events.
**How to avoid:** enforce sync on start/restart and expose explicit sync endpoint.
**Warning signs:** Tool count/schema differs from live server behavior.

### Pitfall 4: Non-actionable error surfacing
**What goes wrong:** Operators see generic failures and cannot fix configs.
**Why it happens:** Exceptions swallowed or truncated.
**How to avoid:** persist last error summary + endpoint response detail for latest failure.
**Warning signs:** `error` status with empty/cryptic message.

## Code Examples

Verified patterns from official sources:

### MCP session initialize + tool discovery
```python
# Source: https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

### MCP tool invocation
```python
# Source: https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/servers/simple-tool/README.md
result = await session.call_tool("fetch", {"url": "https://example.com"})
```

### FastAPI lifespan pattern
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-built startup/shutdown event split | Lifespan async context manager as recommended lifecycle model | FastAPI lifespan adoption (0.93+; current docs) | Cleaner startup/shutdown symmetry for runtime managers |
| Custom MCP protocol glue | Official MCP SDK session/transport primitives | MCP ecosystem maturation (2024-2026 docs/spec) | Faster, safer implementation and protocol alignment |
| Stateless integration config only | Persisted runtime status + error + discovered tool metadata | Modern control-plane UX expectations | Operators can troubleshoot and trust status views |

**Deprecated/outdated:**
- Mixed `lifespan` with independent startup/shutdown assumptions: brittle and easy to misconfigure.

## Open Questions

1. **Should Phase 2 include auto-start of enabled MCP servers at backend boot?**
   - What we know: goal requires manage/run/status, and lifespan pattern supports this cleanly.
   - What's unclear: expected startup policy (all enabled vs lazy start-on-demand).
   - Recommendation: default to auto-start enabled servers; make failures visible via `error` + `last_error`.

2. **How deep should tool schema caching go in this phase?**
   - What we know: Phase 2 requires runtime status/errors; detailed browsing is Phase 3.
   - What's unclear: whether to store full schema now or minimal metadata.
   - Recommendation: store full tool payload now (JSON) but keep UI usage minimal until Phase 3.

## Sources

### Primary (HIGH confidence)
- `/modelcontextprotocol/python-sdk` (Context7) - stdio client/session initialize/list_tools/call_tool patterns
- `https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md` - official SDK client flow
- `https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle` - initialization/lifecycle and timeout guidance
- `/fastapi/fastapi/0.128.0` (Context7) - lifespan recommendation and examples
- `https://fastapi.tiangolo.com/advanced/events/` - canonical FastAPI lifespan docs
- `/websites/sqlalchemy_en_20` (Context7) - AsyncSession transaction patterns
- `https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html` - async ORM transaction/session guidance

### Secondary (MEDIUM confidence)
- `docs/MCP_INTEGRATION_PLAN.md` - local project direction and desired endpoint/UI scope

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing project stack + official MCP/FastAPI/SQLAlchemy docs
- Architecture: HIGH - aligns local architecture and official lifecycle/session patterns
- Pitfalls: MEDIUM - derived from documented lifecycle semantics and expected control-plane failure modes

**Research date:** 2026-02-08
**Valid until:** 2026-03-10 (30 days)
