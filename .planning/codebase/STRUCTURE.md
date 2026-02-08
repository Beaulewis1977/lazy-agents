# Codebase Structure

**Analysis Date:** 2026-02-08

## Directory Layout

```text
lazy-agents/
├── backend/           # FastAPI service, runtime orchestrator, SQLAlchemy models
├── frontend/          # Next.js dashboard and API client
├── docs/              # Product/setup and integration design docs
├── docker-compose.yml # Local multi-service orchestration
├── .env.example       # Shared environment template
└── .planning/         # Generated planning/codebase analysis artifacts
```

## Directory Purposes

**backend/:**
- Purpose: API server and agent orchestration runtime.
- Contains: FastAPI routes (`backend/app/api/`), core config/security/DB (`backend/app/core/`), models (`backend/app/models/`), execution engines (`backend/app/runtime/`), and runtime data (`backend/data/`).
- Key files: `backend/app/main.py`, `backend/app/runtime/agent_executor.py`, `backend/app/runtime/skill_executor.py`, `backend/app/core/database.py`, `backend/requirements.txt`.

**frontend/:**
- Purpose: Browser dashboard for managing agents, skills, integrations, and logs.
- Contains: App Router pages (`frontend/app/`), shared shell/navigation (`frontend/components/`), typed API wrapper (`frontend/lib/api.ts`), global CSS system (`frontend/app/globals.css`).
- Key files: `frontend/app/layout.tsx`, `frontend/app/dashboard/page.tsx`, `frontend/app/agents/[id]/page.tsx`, `frontend/lib/api.ts`, `frontend/package.json`.

**docs/:**
- Purpose: Human documentation and architecture/planning references.
- Contains: setup docs, API docs, integration plans.
- Key files: `docs/getting-started.md`, `docs/MCP_INTEGRATION_PLAN.md`.

**backend/data/:**
- Purpose: Local runtime state and filesystem skill assets.
- Contains: SQLite DB and skill definitions.
- Key files: `backend/data/lazy-agents.db`, `backend/data/skills/code_review/SKILL.md`.

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app creation, router registration, scheduler lifecycle.
- `frontend/app/layout.tsx`: Next.js root layout and global style/font setup.
- `frontend/app/page.tsx`: public landing route.

**Configuration:**
- `.env.example`: canonical env variable template for backend/frontend/deployment.
- `backend/app/core/config.py`: backend runtime settings and env loading behavior.
- `docker-compose.yml`: service graph for frontend/api/redis/worker.
- `frontend/tsconfig.json`: TypeScript compiler config and path aliases.
- `frontend/eslint.config.mjs`: frontend lint profile.

**Core Logic:**
- `backend/app/runtime/agent_executor.py`: execution loop, tool call cycle, execution persistence.
- `backend/app/runtime/llm_client.py`: model-provider adapters.
- `backend/app/runtime/skill_executor.py`: integration-specific tool execution.
- `backend/app/runtime/scheduler.py`: cron parsing and scheduled dispatch.

**Testing:**
- `backend/requirements.txt`: declared test tooling (`pytest`, `pytest-asyncio`, `pytest-cov`).
- `frontend/package.json`: no frontend test script configured.
- Not detected: project test directories/config files such as `backend/tests/`, `frontend/**/__tests__/`, `pytest.ini`, `jest.config.*`, `vitest.config.*`.

## Naming Conventions

**Files:**
- Backend Python modules use `snake_case.py` names: `backend/app/runtime/skill_loader.py`, `backend/app/api/executions.py`.
- Next.js routes use `page.tsx` convention within route folders: `frontend/app/integrations/page.tsx`, `frontend/app/skills/[id]/page.tsx`.

**Directories:**
- Backend directories are capability/layer based: `backend/app/api`, `backend/app/core`, `backend/app/models`, `backend/app/runtime`.
- Frontend directories are route-segment based under App Router: `frontend/app/agents/new`, `frontend/app/agents/[id]`, `frontend/app/dashboard`.

## Where to Add New Code

**New Feature:**
- Primary code: backend endpoint in `backend/app/api/` plus runtime/service logic in `backend/app/runtime/`.
- Tests: add backend tests under `backend/tests/` and frontend tests under `frontend/__tests__/` (currently not present; create these directories).

**New Component/Module:**
- Implementation: page-level UI in `frontend/app/<route>/page.tsx`; shared reusable UI in `frontend/components/`.

**Utilities:**
- Shared helpers: frontend helper modules in `frontend/lib/`; backend cross-cutting helpers in `backend/app/core/`.

## Special Directories

**`frontend/.next`:**
- Purpose: Next.js build/dev artifacts.
- Generated: Yes.
- Committed: No (ignored by `frontend/.gitignore`).

**`frontend/node_modules`:**
- Purpose: frontend package installation tree.
- Generated: Yes.
- Committed: No (ignored by `frontend/.gitignore`).

**`backend/venv`:**
- Purpose: local Python virtual environment.
- Generated: Yes.
- Committed: No (environment-local runtime dependency cache).

**`backend/data`:**
- Purpose: local persistent runtime data (SQLite DB + skill files).
- Generated: Mixed (database is runtime-generated; skill markdowns are source assets).
- Committed: Yes for skill files in `backend/data/skills/`; runtime DB commit policy should be treated as environment-specific.

**`frontend/.git`:**
- Purpose: nested git metadata for frontend sub-repository.
- Generated: No.
- Committed: Yes (repository metadata for `frontend/` itself).

---

*Structure analysis: 2026-02-08*
