# Coding Conventions

**Analysis Date:** 2026-02-08

## Naming Patterns

**Files:**
- Backend Python modules use `snake_case.py` naming: `backend/app/runtime/agent_executor.py`, `backend/app/api/integrations.py`.
- Next.js route files use App Router `page.tsx` convention under route directories: `frontend/app/dashboard/page.tsx`, `frontend/app/skills/[id]/page.tsx`.
- Shared frontend modules use lower-case names: `frontend/lib/api.ts`, `frontend/components/DashboardLayout.tsx`.

**Functions:**
- Python functions and methods use `snake_case`: `verify_api_key` in `backend/app/core/security.py`, `list_integrations` in `backend/app/api/integrations.py`.
- React component functions use `PascalCase` and event handlers use `handleX` style: `IntegrationsPage` and `handleCreate` in `frontend/app/integrations/page.tsx`.

**Variables:**
- Frontend variables use `camelCase`: `showCreate`, `integrationName` in `frontend/app/integrations/page.tsx`.
- Backend variables use `snake_case`: `integration_data`, `type_info` in `backend/app/api/integrations.py`.

**Types:**
- Pydantic/ORM classes use `PascalCase`: `AgentCreate` in `backend/app/api/agents.py`, `ExecutionStep` in `backend/app/models/execution.py`.
- TypeScript interfaces use `PascalCase`: `Agent`, `ExecutionStats` in `frontend/lib/api.ts`.

## Code Style

**Formatting:**
- Frontend formatting is lint-driven through ESLint config in `frontend/eslint.config.mjs`.
- Backend formatter/linter/type-check tools (`black`, `ruff`, `mypy`) are declared in `backend/requirements.txt`; repository-level config files are not detected.

**Linting:**
- Frontend uses `eslint-config-next` core-web-vitals + TypeScript rules in `frontend/eslint.config.mjs`.
- Frontend lint command is `npm run lint` in `frontend/package.json`.

## Import Organization

**Order:**
1. Standard library imports first (for example `import json`, `from typing import ...` in `backend/app/runtime/agent_executor.py`).
2. Third-party imports second (`from fastapi import ...`, `from sqlalchemy ...` in `backend/app/api/agents.py`).
3. Local project imports last (`from app.core.database ...`, `from app.models.agent ...` in `backend/app/api/agents.py`).

**Path Aliases:**
- Frontend uses `@/*` alias mapped to project root in `frontend/tsconfig.json` and consumed as `@/components/DashboardLayout`/`@/lib/api` across `frontend/app/*.tsx`.

## Error Handling

**Patterns:**
- API boundary uses `HTTPException` with explicit status codes for expected failures in `backend/app/api/*.py`.
- Runtime services catch broad exceptions, persist failure status, and continue logging context in `backend/app/runtime/agent_executor.py` and `backend/app/runtime/skill_executor.py`.

## Logging

**Framework:** `structlog` for API lifecycle logs (`backend/app/main.py`) plus standard `logging` in modules like `backend/app/runtime/scheduler.py` and `backend/app/api/websocket.py`.

**Patterns:**
- Emit structured startup/shutdown/scheduling logs from backend lifecycle methods in `backend/app/main.py` and `backend/app/runtime/scheduler.py`.
- Emit execution-scoped logs through callback dispatch in `backend/app/runtime/agent_executor.py`, streamed via `backend/app/api/websocket.py`.
- Frontend pages use `console.log`/`console.error` sparingly for client diagnostics (`frontend/app/agents/[id]/page.tsx`).

## Comments

**When to Comment:**
- Backend uses section-divider comments and focused explanatory comments for API schemas/endpoints (`backend/app/api/integrations.py`, `backend/app/api/skills.py`).
- Frontend uses JSX block comments for structural sections (`frontend/app/page.tsx`, `frontend/components/DashboardLayout.tsx`).

**JSDoc/TSDoc:**
- Limited usage; most documentation is via Python docstrings in backend (`backend/app/api/agents.py`, `backend/app/runtime/skill_loader.py`) rather than JSDoc/TSDoc blocks in frontend.

## Function Design

**Size:**
- Route handlers are generally medium sized and scoped to one endpoint in `backend/app/api/*.py`.
- Some UI components are large multi-responsibility pages (for example `frontend/app/agents/[id]/page.tsx` and `frontend/app/skills/[id]/page.tsx`).

**Parameters:**
- API inputs are strongly typed with Pydantic models for create/update payloads in `backend/app/api/agents.py`, `backend/app/api/integrations.py`, and `backend/app/api/skills.py`.
- Frontend handlers pass typed payload objects through centralized API methods in `frontend/lib/api.ts`.

**Return Values:**
- Backend endpoints return Pydantic response models or dict payloads with consistent status/message fields (`backend/app/api/executions.py`, `backend/app/api/agents.py`).
- Frontend API layer returns typed `Promise<T>` values from `fetchAPI<T>` in `frontend/lib/api.ts`.

## Module Design

**Exports:**
- Frontend route modules default-export one page component (`export default function ...`) in `frontend/app/**/*.tsx`.
- API helper module exports grouped domain clients as named constants (`agentsAPI`, `skillsAPI`, etc.) in `frontend/lib/api.ts`.
- Backend modules expose classes/functions directly; package-level re-exports are minimal and explicit (`backend/app/models/__init__.py`, `backend/app/runtime/__init__.py`).

**Barrel Files:**
- Limited use. Backend has small `__init__.py` barrels in `backend/app/models/__init__.py` and `backend/app/runtime/__init__.py`.
- Frontend does not use broad barrel exports for pages/components.

---

*Convention analysis: 2026-02-08*
