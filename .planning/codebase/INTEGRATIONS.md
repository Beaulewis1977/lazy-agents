# External Integrations

**Analysis Date:** 2026-02-08

## APIs & External Services

**LLM Providers:**
- OpenAI - Chat completions and streaming for GPT/o-series models in `backend/app/runtime/llm_client.py`.
  - SDK/Client: `httpx` direct REST calls to `https://api.openai.com/v1`.
  - Auth: `OPENAI_API_KEY` (or integration credential `api_key` stored via `backend/app/api/integrations.py`).
- Anthropic - Claude chat and streaming in `backend/app/runtime/llm_client.py`.
  - SDK/Client: `httpx` direct REST calls to `https://api.anthropic.com/v1`.
  - Auth: `ANTHROPIC_API_KEY` (or integration credential `api_key`).
- Google Gemini - content generation in `backend/app/runtime/llm_client.py`.
  - SDK/Client: `httpx` direct REST calls to `https://generativelanguage.googleapis.com/v1beta`.
  - Auth: `GOOGLE_API_KEY` (or integration credential `api_key`).

**Productivity/Chat Integrations:**
- GitHub - API tests and skill execution in `backend/app/api/integrations.py` and `backend/app/runtime/skill_executor.py`.
  - SDK/Client: `httpx` to `api.github.com`.
  - Auth: `GITHUB_TOKEN` or integration credential `token`.
- Discord - API tests and skill execution in `backend/app/api/integrations.py` and `backend/app/runtime/skill_executor.py`.
  - SDK/Client: `httpx` to `discord.com/api/v10`.
  - Auth: `DISCORD_BOT_TOKEN` or integration credential `bot_token`.
- Slack - API tests and skill execution in `backend/app/api/integrations.py` and `backend/app/runtime/skill_executor.py`.
  - SDK/Client: `httpx` to `slack.com/api`.
  - Auth: `SLACK_BOT_TOKEN` plus `SLACK_SIGNING_SECRET` for signed requests.
- Notion - integration type is declared in `backend/app/api/integrations.py` and env var is declared in `backend/app/core/config.py`.
  - SDK/Client: `notion-client` declared in `backend/requirements.txt`.
  - Auth: `NOTION_API_KEY`.

**Generic Integration Surface:**
- HTTP tool integration - generic outbound HTTP requests from skills in `backend/app/runtime/skill_executor.py`.
  - SDK/Client: `httpx`.
  - Auth: Per-request headers passed in skill parameters.

**Planned Integration Architecture (Design-Only):**
- Model Context Protocol (MCP) servers are specified as a planned extension in `docs/MCP_INTEGRATION_PLAN.md`.
  - Planned backend surface: `backend/app/mcp/` manager/registry/executor modules and `backend/app/api/mcp.py` routes (not detected in current codebase).
  - Planned frontend surface: `frontend/app/integrations/mcp/` management UI (not detected in current codebase).

## Data Storage

**Databases:**
- SQLite (default) via SQLAlchemy async engine in `backend/app/core/database.py`.
  - Connection: `DATABASE_URL` (`sqlite+aiosqlite:///./data/lazy-agents.db` default in `backend/app/core/config.py`).
  - Client: SQLAlchemy ORM models in `backend/app/models/*.py`.
- PostgreSQL (optional) supported by URL and `asyncpg` dependency in `backend/requirements.txt` and `.env.example`.
  - Connection: `DATABASE_URL`.
  - Client: SQLAlchemy async engine in `backend/app/core/database.py`.

**File Storage:**
- Local filesystem only (`backend/data/`, `backend/data/skills/`) with file operations in `backend/app/runtime/skill_executor.py`.

**Caching:**
- Redis optional service configured in `docker-compose.yml` with `REDIS_URL` in `.env.example` and `backend/app/core/config.py`.

## Authentication & Identity

**Auth Provider:**
- Custom API key auth (`X-API-Key`) implemented in `backend/app/core/security.py` and attached to routers in `backend/app/api/*.py`.
  - Implementation: Header-based shared key check via `verify_api_key`; disabled when `API_KEY` is unset.

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry/Datadog/Rollbar config files or SDK initialization).

**Logs:**
- Structured backend logging via `structlog` in `backend/app/main.py`.
- Real-time log streaming over WebSocket endpoints in `backend/app/api/websocket.py`.

## CI/CD & Deployment

**Hosting:**
- Self-hosted Docker deployment model (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`).

**CI Pipeline:**
- Not detected (no `.github/workflows/`, GitLab CI, or other pipeline config in project root).

## Environment Configuration

**Required env vars:**
- Core app/security: `APP_ENV`, `APP_DEBUG`, `API_URL`, `SECRET_KEY`, `API_KEY` (`.env.example`, `backend/app/core/config.py`).
- Database: `DATABASE_URL` (`.env.example`, `backend/app/core/config.py`).
- LLM providers: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`, `OLLAMA_BASE_URL` (`.env.example`, `backend/app/core/config.py`).
- Integrations: `GITHUB_TOKEN`, `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `NOTION_API_KEY` (`.env.example`, `backend/app/core/config.py`).
- Frontend API routing: `NEXT_PUBLIC_API_URL` (`frontend/lib/api.ts`, `docker-compose.yml`).

**Secrets location:**
- Development: plaintext env files (`.env` at repo root for Compose, `backend/.env` for direct backend runtime).
- Runtime secrets in DB are encrypted before persistence (`backend/app/core/security.py`, `backend/app/models/integration.py`, `backend/app/api/integrations.py`).

## Webhooks & Callbacks

**Incoming:**
- WebSocket endpoints for logs/execution streams: `/ws/logs` and `/ws/executions/{execution_id}/stream` in `backend/app/api/websocket.py`.
- HTTP webhook endpoints for third-party callbacks are not detected in `backend/app/api/`.

**Outgoing:**
- Outbound API calls to OpenAI, Anthropic, Google Gemini, GitHub, Discord, and Slack from `backend/app/runtime/llm_client.py`, `backend/app/runtime/skill_executor.py`, and `backend/app/api/integrations.py`.

---

*Integration audit: 2026-02-08*
