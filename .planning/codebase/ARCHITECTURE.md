# Architecture

**Analysis Date:** 2026-02-08

## Pattern Overview

**Overall:** Layered modular monolith with split frontend/backend applications.

**Key Characteristics:**
- UI and API are separated by deployment unit (`frontend/` and `backend/`) and communicate over HTTP/WebSocket (`frontend/lib/api.ts`, `backend/app/main.py`, `backend/app/api/websocket.py`).
- Backend business logic is centralized in runtime services (`backend/app/runtime/agent_executor.py`, `backend/app/runtime/skill_executor.py`, `backend/app/runtime/llm_client.py`) and exposed by thin route handlers in `backend/app/api/*.py`.
- Persistence uses SQLAlchemy ORM models as shared schema objects (`backend/app/models/*.py`) with async session dependency injection from `backend/app/core/database.py`.

## Layers

**Frontend Presentation Layer:**
- Purpose: Render dashboard UI, collect user input, and display execution/integration state.
- Location: `frontend/app/`, `frontend/components/`, `frontend/app/globals.css`.
- Contains: App Router pages, client components, CSS design system, inline page-level interaction logic.
- Depends on: API wrapper in `frontend/lib/api.ts`, Next.js runtime (`frontend/app/layout.tsx`).
- Used by: End users through browser routes like `frontend/app/dashboard/page.tsx` and `frontend/app/agents/[id]/page.tsx`.

**Frontend API Client Layer:**
- Purpose: Centralize HTTP calls and response typing.
- Location: `frontend/lib/api.ts`.
- Contains: `fetchAPI` helper plus domain APIs (`agentsAPI`, `skillsAPI`, `integrationsAPI`, `executionsAPI`, `healthAPI`).
- Depends on: Backend base URL env var (`NEXT_PUBLIC_API_URL`) and browser `fetch`.
- Used by: All dashboard pages in `frontend/app/**/*.tsx`.

**Backend API Layer:**
- Purpose: Validate request/response payloads and expose REST/WebSocket endpoints.
- Location: `backend/app/api/*.py` registered in `backend/app/main.py`.
- Contains: CRUD routes for agents, skills, integrations, executions, health, and WebSocket log streams.
- Depends on: Core dependencies (`backend/app/core/database.py`, `backend/app/core/security.py`) and runtime services.
- Used by: Frontend API client and external API consumers.

**Backend Runtime/Orchestration Layer:**
- Purpose: Execute agent loops, route model/tool calls, schedule recurring runs, and load filesystem skills.
- Location: `backend/app/runtime/*.py`.
- Contains: `AgentExecutor`, LLM clients, skill executor registry, scheduler, skill loader.
- Depends on: ORM models (`backend/app/models/*.py`), encrypted integration credentials (`backend/app/core/security.py`), and external APIs.
- Used by: API layer (`backend/app/api/agents.py`, `backend/app/main.py`).

**Persistence Layer:**
- Purpose: Store agents, integrations, skills, executions, and execution steps.
- Location: `backend/app/models/*.py`, `backend/app/core/database.py`, data file `backend/data/lazy-agents.db`.
- Contains: SQLAlchemy declarative models and async session factory.
- Depends on: `DATABASE_URL` configuration in `backend/app/core/config.py`.
- Used by: API routes and runtime services.

## Data Flow

**Dashboard CRUD Flow:**

1. UI page triggers API call via `frontend/lib/api.ts` (for example `agentsAPI.list()` from `frontend/app/agents/page.tsx`).
2. FastAPI route in `backend/app/api/agents.py` queries ORM models through async session (`Depends(get_db)` from `backend/app/core/database.py`).
3. Route returns Pydantic response model; frontend state updates and re-renders.

**Agent Execution Flow:**

1. Frontend triggers `POST /api/agents/{id}/run` using `agentsAPI.run()` in `frontend/lib/api.ts`.
2. Route `run_agent` in `backend/app/api/agents.py` instantiates `AgentExecutor` from `backend/app/runtime/agent_executor.py`.
3. `AgentExecutor` loads agent skills/integrations from DB (`backend/app/models/*.py`), selects provider client (`backend/app/runtime/llm_client.py`), executes tool calls through `skill_executor_registry` (`backend/app/runtime/skill_executor.py`), records `Execution` + `ExecutionStep` rows, and returns output.

**Scheduled Execution Flow:**

1. `backend/app/main.py` starts global scheduler `agent_scheduler` from `backend/app/runtime/scheduler.py` during app lifespan.
2. Active agents with schedules are loaded from DB and registered (`backend/app/main.py`).
3. Scheduler callback executes `AgentExecutor.execute(..., trigger="schedule")` and logs status through WebSocket emitters in `backend/app/api/websocket.py`.

**State Management:**
- Frontend state is local component state (`useState`/`useEffect`) in route files like `frontend/app/dashboard/page.tsx`.
- Backend state is persisted in SQLAlchemy-backed DB models in `backend/app/models/*.py`; runtime in-memory state exists only during each execution loop (`ExecutionContext` in `backend/app/runtime/agent_executor.py`).

## Key Abstractions

**Agent Execution Context (`ExecutionContext`):**
- Purpose: Package execution-time agent, skills, integrations, input, and runtime metadata.
- Examples: `backend/app/runtime/agent_executor.py`.
- Pattern: Dataclass context object passed through orchestration methods.

**Skill Execution Registry (`SkillExecutorRegistry`):**
- Purpose: Route skill IDs to integration-specific executors.
- Examples: `backend/app/runtime/skill_executor.py`.
- Pattern: Prefix-based registry (`github.*`, `discord.*`, `http.*`, `file.*`, `shell.*`).

**LLM Provider Adapter (`BaseLLMClient` + implementations):**
- Purpose: Normalize chat API access across OpenAI/Anthropic/Google.
- Examples: `backend/app/runtime/llm_client.py`.
- Pattern: Strategy interface with provider-specific client classes selected by model prefix.

**Filesystem Skill Loader (`SkillLoader`):**
- Purpose: Parse Markdown/YAML skill definitions and convert to DB schema.
- Examples: `backend/app/runtime/skill_loader.py`, `backend/data/skills/`.
- Pattern: Loader + transformer (`to_db_format`) with frontmatter parsing and optional template/reference ingestion.

## Entry Points

**Backend API Server:**
- Location: `backend/app/main.py`.
- Triggers: `uvicorn app.main:app` from `backend/Dockerfile` or local dev command in `README.md`.
- Responsibilities: app bootstrapping, DB init, router registration, CORS, scheduler startup/shutdown.

**Frontend Application Root:**
- Location: `frontend/app/layout.tsx` and `frontend/app/page.tsx`.
- Triggers: Next.js runtime (`next dev`, `next build`, `next start`) from `frontend/package.json`.
- Responsibilities: global layout/style setup and route rendering.

**Container Orchestration:**
- Location: `docker-compose.yml`.
- Triggers: `docker compose up -d`.
- Responsibilities: start frontend, API, Redis, and worker services with service wiring.

## Error Handling

**Strategy:** Mixed explicit HTTP exceptions at API boundary and broad exception capture in runtime loops.

**Patterns:**
- API routes raise `HTTPException` with typed status codes for not found/validation/forbidden paths (`backend/app/api/agents.py`, `backend/app/api/skills.py`, `backend/app/api/integrations.py`, `backend/app/api/executions.py`).
- Runtime executor catches broad exceptions, marks execution failed, and stores error message in DB (`backend/app/runtime/agent_executor.py`).

## Cross-Cutting Concerns

**Logging:** Structured backend logs via `structlog` in `backend/app/main.py`; live log fanout via WebSocket manager in `backend/app/api/websocket.py`.
**Validation:** Pydantic request/response models in API modules (`backend/app/api/*.py`) and field constraints via `Field(...)` in `backend/app/api/agents.py`.
**Authentication:** Shared API key dependency `verify_api_key` in `backend/app/core/security.py`, applied to operational routers through `APIRouter(dependencies=[Depends(verify_api_key)])`.
**Extensibility Roadmap:** MCP-based universal integration architecture is documented in `docs/MCP_INTEGRATION_PLAN.md`; planned modules/routes (`backend/app/mcp/`, `backend/app/api/mcp.py`, `frontend/app/integrations/mcp/`) are not detected in current implementation.

---

*Architecture analysis: 2026-02-08*
