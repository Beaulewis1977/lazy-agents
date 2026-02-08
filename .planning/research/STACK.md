# Stack Research

**Domain:** Self-hosted AI agent orchestration control plane (brownfield MCP expansion)
**Researched:** 2026-02-08
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 16.1.6 | Frontend control plane UI | Already in production codebase; App Router patterns, runtime env guidance, and CSP guidance are well documented for secure deployment. |
| React | 19.2.4 | UI composition/runtime | Matches current frontend stack and avoids rewrite risk. |
| FastAPI | 0.128.4 | Backend API surface and runtime control plane endpoints | Existing backend foundation; strong dependency-based auth patterns and OAuth/JWT security guidance. |
| SQLAlchemy | 2.0.46 | Persistence model and async DB access | Already used for core models; natural fit for adding `mcp_servers` and related metadata. |
| MCP Python SDK (`mcp`) | 1.26.0 | MCP client/session transport and protocol handling | Official SDK supports `stdio` and streamable HTTP patterns with initialize/list_tools/call_tool workflows. |
| Docker Compose | v2 plugin line | Required self-host deployment target | User-selected v1 deployment target is single-VM Compose; official docs are mature and operationally simple. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.12.5 | Request/response validation and config safety | Keep API contracts explicit for MCP config schemas and tool call payloads. |
| Uvicorn | 0.40.0 | ASGI serving for FastAPI | Existing runtime entrypoint; stable for websocket + API mixed traffic. |
| APScheduler | 3.11.2 | Scheduled agent execution | Continue current scheduling flow; do not replace during MCP phase. |
| `@modelcontextprotocol/sdk` | 1.26.0 | Optional TS-side MCP compatibility tooling | Useful for validating interoperability and future frontend/server-side utilities. |
| `cryptography` | 46.0.4 | Secret encryption at rest | Aligns with existing encrypted credential storage model. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Docker Compose | Local/prod-like orchestration | Keep one-command setup for solo/small-team operators. |
| pytest + pytest-asyncio | Backend verification | Needed to harden MCP process lifecycle and dispatch reliability. |
| ESLint (Next.js) | Frontend quality gate | Preserve existing lint flow and avoid UI regression debt. |

## Installation

```bash
# Backend runtime updates
pip install "fastapi==0.128.4" "sqlalchemy==2.0.46" "pydantic==2.12.5" \
  "uvicorn==0.40.0" "mcp==1.26.0"

# Frontend/runtime alignment
npm install next@16.1.6 react@19.2.4 @modelcontextprotocol/sdk@1.26.0
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Extend FastAPI monolith | Split dedicated MCP microservice | Use only if MCP process isolation/scale demands exceed monolith boundaries. |
| MCP Python SDK | Hand-rolled JSON-RPC implementation | Only for very specialized protocol control; otherwise unnecessary risk. |
| Compose single VM | Kubernetes-first | Defer until post-v1 scale/ops complexity demands it. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Custom ad-hoc tool protocol between agents and integrations | Reinvents MCP and increases compatibility debt | Standard MCP transports + SDK primitives |
| Secrets in browser localStorage or plaintext config | High leakage risk and poor operator security posture | Encrypted backend persistence + masked UI inputs |
| Broad always-on dangerous execution defaults | Violates secure-by-default expectation | Explicitly gated/validated execution paths and config |

## Stack Patterns by Variant

**If running local development only:**
- Keep SQLite + Compose defaults.
- Because fastest feedback and least setup overhead.

**If running shared team environment on one VM:**
- Use Postgres-backed `DATABASE_URL`, enforce API auth key, and keep secrets server-side only.
- Because it improves concurrency and reduces accidental secret leakage.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `next@16.1.6` | `react@19.2.4` | Current frontend line in this repository. |
| `fastapi@0.128.4` | `pydantic@2.12.5` | Modern FastAPI v0.12x line uses Pydantic v2. |
| `mcp@1.26.0` | MCP protocol architecture/spec docs | SDK examples show initialize/list/call flow for stdio and HTTP transports. |

## Sources

- Context7 `/fastapi/fastapi` — security dependency and JWT/OAuth docs
- Context7 `/vercel/next.js/v16.1.5` — env and CSP deployment guidance
- Context7 `/modelcontextprotocol/python-sdk` — session init, `list_tools`, `call_tool`, stdio/http usage
- https://modelcontextprotocol.io/docs/learn/architecture — protocol architecture
- https://modelcontextprotocol.io/specification/2025-03-26/architecture — host/client/server principles
- https://nextjs.org/docs/app/guides/environment-variables — runtime/server env handling
- https://nextjs.org/docs/app/guides/content-security-policy — CSP patterns
- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ — auth/token security tutorial
- https://docs.docker.com/compose/ — Compose deployment docs
- https://pypi.org/pypi/fastapi/json, https://pypi.org/pypi/mcp/json, https://pypi.org/pypi/sqlalchemy/json — current package versions
- `npm view` package registry lookups for `next`, `react`, `@modelcontextprotocol/sdk`

---
*Stack research for: self-hosted AI agent orchestration control plane*
*Researched: 2026-02-08*
