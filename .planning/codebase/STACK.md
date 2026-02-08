# Technology Stack

**Analysis Date:** 2026-02-08

## Languages

**Primary:**
- Python 3.11 - Backend API/runtime in `backend/app/main.py`, `backend/app/api/*.py`, and `backend/app/runtime/*.py`.
- TypeScript (strict mode) - Frontend app code in `frontend/app/*.tsx`, `frontend/components/*.tsx`, and `frontend/lib/api.ts` (`frontend/tsconfig.json`).

**Secondary:**
- SQL (SQLite default, PostgreSQL optional) - Connection configured via `DATABASE_URL` in `backend/app/core/config.py` and `.env` templates in `.env.example`.
- CSS - Global design system and utility classes in `frontend/app/globals.css`.
- YAML frontmatter + Markdown - Skill definitions parsed in `backend/app/runtime/skill_loader.py` and stored in `backend/data/skills/`.

## Runtime

**Environment:**
- Python 3.11 (`python:3.11-slim`) for backend containers in `backend/Dockerfile`.
- Node.js 20 (`node:20-alpine`) for frontend build/runtime in `frontend/Dockerfile`.

**Package Manager:**
- npm (frontend) - `frontend/package-lock.json` present.
- pip (backend) - lockfile not detected (`backend/requirements.txt` exists; no lockfile detected).

## Frameworks

**Core:**
- FastAPI (>=0.109.0) - API server and routing in `backend/app/main.py` and `backend/app/api/*.py`.
- SQLAlchemy 2.x async - ORM/session layer in `backend/app/core/database.py` and `backend/app/models/*.py`.
- Next.js 16.1.6 (App Router) - Web dashboard in `frontend/app/` with metadata and layout in `frontend/app/layout.tsx`.
- React 19.2.3 - Client UI/state logic in `frontend/app/**/*.tsx` and `frontend/components/DashboardLayout.tsx`.

**Testing:**
- pytest/pytest-asyncio/pytest-cov declared in `backend/requirements.txt`.
- No active test runner config detected in project files (`pytest.ini`, `jest.config.*`, `vitest.config.*` not detected).

**Build/Dev:**
- Uvicorn (>=0.27.0) - backend server command in `backend/Dockerfile`.
- ESLint 9 + `eslint-config-next` - frontend linting config in `frontend/eslint.config.mjs`.
- Tailwind CSS v4 packages are installed in `frontend/package.json` (`tailwindcss`, `@tailwindcss/postcss`) with PostCSS config in `frontend/postcss.config.mjs`.
- Docker Compose orchestrates local services in `docker-compose.yml`.

## Key Dependencies

**Critical:**
- `openai`, `anthropic`, `google-generativeai` - model provider integrations in `backend/app/runtime/llm_client.py`.
- `httpx` - outbound API calls across integrations and runtime (`backend/app/runtime/llm_client.py`, `backend/app/runtime/skill_executor.py`, `backend/app/api/integrations.py`).
- `cryptography` (`Fernet`) - encrypt/decrypt integration credentials in `backend/app/core/security.py`.
- `apscheduler` + `croniter` - schedule parsing/execution in `backend/app/runtime/scheduler.py`.

**Infrastructure:**
- `aiosqlite` / optional `asyncpg` - async DB drivers configured via `DATABASE_URL` in `backend/app/core/config.py`.
- `redis` Python client + Redis service image - optional queue/cache infra configured in `docker-compose.yml` and `backend/requirements.txt`.
- `structlog` - structured JSON logging setup in `backend/app/main.py`.

## Configuration

**Environment:**
- Backend settings are centralized in `backend/app/core/config.py` (`pydantic-settings`), loading `backend/.env` by default.
- Root `.env.example` defines full environment contract for app, DB, LLM providers, integrations, and security (`.env.example`).
- Frontend backend URL is configured through `NEXT_PUBLIC_API_URL` in `frontend/lib/api.ts` and `docker-compose.yml`.

**Build:**
- Frontend build/runtime config: `frontend/next.config.ts`, `frontend/tsconfig.json`, `frontend/postcss.config.mjs`, `frontend/eslint.config.mjs`, `frontend/Dockerfile`.
- Backend runtime/build config: `backend/Dockerfile`, `backend/requirements.txt`, `backend/app/main.py`.
- Multi-service local deployment: `docker-compose.yml`.

## Platform Requirements

**Development:**
- Docker + Docker Compose documented in `README.md` and `docs/getting-started.md`.
- For non-container local runs: Python venv + pip (`backend/requirements.txt`) and Node/npm (`frontend/package.json`) per `README.md`.

**Production:**
- Containerized deployment target via Docker images and Compose services (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`).
- Backend expects externalized secrets/env vars and database URL in deployment environment (`backend/app/core/config.py`, `.env.example`).

---

*Stack analysis: 2026-02-08*
