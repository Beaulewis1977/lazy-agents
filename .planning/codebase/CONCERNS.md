# Codebase Concerns

**Analysis Date:** 2026-02-08

## Tech Debt

**Frontend page complexity (`skills` + `agent detail` pages):**
- Issue: UI, data-fetching, mutation handling, and styling are tightly mixed in single large files.
- Files: `frontend/app/skills/[id]/page.tsx`, `frontend/app/agents/[id]/page.tsx`, `frontend/app/skills/page.tsx`.
- Impact: Higher regression risk when modifying one behavior; hard to test and reason about state transitions.
- Fix approach: Extract hooks (`useSkillDetail`, `useAgentDetail`) and split view sections into smaller components under `frontend/components/`.

**Execution pipeline concentration:**
- Issue: The agent orchestration loop, skill execution plumbing, DB writes, and log callbacks are concentrated in one class.
- Files: `backend/app/runtime/agent_executor.py`, `backend/app/runtime/skill_executor.py`.
- Impact: Small execution-path changes can introduce cross-cutting breakage (prompting, tool calls, persistence, logging).
- Fix approach: Split into focused services (context loader, loop engine, step recorder, provider selector) and add contract tests per service.

**Deployment/runtime drift:**
- Issue: Compose declares a worker command that references a module not present in source.
- Files: `docker-compose.yml`, `backend/app/` (no `worker.py`).
- Impact: `worker` service fails at startup, reducing confidence in background-processing architecture.
- Fix approach: Add `backend/app/worker.py` or remove/replace the worker service until implementation exists.

## Known Bugs

**Integration test API response contract mismatch:**
- Symptoms: Frontend expects `{ success: boolean, message: string }`; backend returns `{ status: "ok"|"error", message: string }`.
- Files: `frontend/lib/api.ts`, `frontend/app/integrations/page.tsx`, `backend/app/api/integrations.py`.
- Trigger: Click “Test” in integrations UI.
- Workaround: None reliable in UI; response mapping should be normalized in backend or frontend.

**Custom skill creation request is invalid for backend schema:**
- Symptoms: Frontend create form omits required `implementation` field that backend enforces.
- Files: `frontend/app/skills/page.tsx`, `backend/app/api/skills.py`.
- Trigger: Create custom skill from dashboard modal.
- Workaround: Use `POST /api/skills/load-from-path` instead of direct custom-skill form creation.

**Worker container cannot start:**
- Symptoms: Compose worker command points to `python -m app.worker`, but module is missing.
- Files: `docker-compose.yml`, `backend/app/`.
- Trigger: Start stack with `docker compose up` including worker service.
- Workaround: Run only `frontend`, `api`, and `redis` services, or remove worker service.

**Agent detail page uses incorrect “Created” source field:**
- Symptoms: “Created” date is derived from `last_run_at` fallback, not creation time.
- Files: `frontend/app/agents/[id]/page.tsx`.
- Trigger: Open any agent details page.
- Workaround: None in UI; backend config endpoint would need a created timestamp field or frontend should relabel value.

**Agent detail logs hardcode localhost WebSocket endpoint:**
- Symptoms: Logs stream uses `ws://localhost:8000/ws/logs` while computing but not using dynamic `wsUrl`.
- Files: `frontend/app/agents/[id]/page.tsx`.
- Trigger: Open logs tab in non-localhost deployment.
- Workaround: Manual code change to use dynamic URL from current host/env.

## Security Considerations

**API auth can be fully bypassed by missing config:**
- Risk: All protected routes become publicly accessible when `API_KEY` is unset.
- Files: `backend/app/core/security.py`, `backend/app/core/config.py`.
- Current mitigation: Optional API key check when configured.
- Recommendations: Fail closed in non-dev mode (`APP_ENV != development`), enforce startup validation for `API_KEY` and `SECRET_KEY`.

**Weak key derivation for secret encryption:**
- Risk: Encryption key is derived by truncating/padding `SECRET_KEY`, which weakens key handling.
- Files: `backend/app/core/security.py`.
- Current mitigation: Fernet encryption wrapper is used for stored integration credentials.
- Recommendations: Use proper KDF (for example PBKDF2/HKDF + salt) and rotate secrets via migration.

**Sensitive tokens stored in browser localStorage:**
- Risk: XSS exposure of provider keys and API key in browser storage.
- Files: `frontend/app/settings/page.tsx`.
- Current mitigation: None beyond local-only browser storage.
- Recommendations: Move secret persistence to backend encrypted store and use masked/tokenized retrieval UX.

## Performance Bottlenecks

**Large client-rendered pages with broad state scope:**
- Problem: Very large single files combine multiple tabs/features and rerender broad state on interaction.
- Files: `frontend/app/skills/[id]/page.tsx`, `frontend/app/agents/[id]/page.tsx`.
- Cause: Monolithic component design, mixed concern boundaries.
- Improvement path: Componentize tab panels and memoize heavy sections; split CSS from component logic.

**Execution polling/data fanout patterns pull full lists:**
- Problem: Pages request up to 100 executions and full agent lists at once.
- Files: `frontend/app/executions/page.tsx`, `frontend/app/dashboard/page.tsx`, `frontend/lib/api.ts`.
- Cause: No pagination/incremental loading in UI state flows.
- Improvement path: Add server-side pagination controls and cursor-based loading.

**In-process websocket buffering:**
- Problem: Log buffering and subscriber tracking live in API process memory.
- Files: `backend/app/api/websocket.py`.
- Cause: No external pub/sub or backpressure controls.
- Improvement path: Move log fanout to Redis pub/sub and cap per-subscriber queue depth.

## Fragile Areas

**Agent orchestration runtime:**
- Files: `backend/app/runtime/agent_executor.py`, `backend/app/runtime/llm_client.py`, `backend/app/runtime/skill_executor.py`.
- Why fragile: Multi-provider model selection, tool-call parsing, DB writes, and callback logging are tightly coupled.
- Safe modification: Change one concern at a time with integration tests around `AgentExecutor.execute` and tool-call extraction.
- Test coverage: No in-repo runtime tests detected.

**Skill management flow:**
- Files: `backend/app/api/skills.py`, `backend/app/runtime/skill_loader.py`, `frontend/app/skills/page.tsx`.
- Why fragile: Multiple entry paths (builtin/db/filesystem) and schema transformations with limited validation feedback.
- Safe modification: Add schema contract checks for create/update/load endpoints before UI changes.
- Test coverage: No endpoint/loader tests detected.

**Scheduling lifecycle:**
- Files: `backend/app/main.py`, `backend/app/runtime/scheduler.py`.
- Why fragile: Startup wiring, schedule loading, and callback linkage happen during app lifespan with minimal guardrails.
- Safe modification: Keep scheduler API stable and test startup/shutdown + schedule recovery behaviors.
- Test coverage: No scheduler tests detected.

## Scaling Limits

**SQLite default persistence:**
- Current capacity: Single-node, file-based DB (`backend/data/lazy-agents.db`).
- Limit: Write concurrency and operational resilience degrade under higher parallel execution volume.
- Scaling path: Move to managed PostgreSQL (`DATABASE_URL`) and add migration/versioning workflow.

**In-memory scheduler job store:**
- Current capacity: Schedules live only in process memory (`MemoryJobStore`).
- Limit: Process restart drops scheduled jobs until reload cycle; multi-instance coordination is absent.
- Scaling path: Use persistent APScheduler job store (Redis/SQL) with leader-election strategy.

**Single-process WebSocket manager:**
- Current capacity: Subscribers and log buffer reside in one API process.
- Limit: Horizontal scaling breaks unified log stream consistency.
- Scaling path: Externalize event bus (Redis/NATS) and stateless WebSocket workers.

## Dependencies at Risk

**Unused heavy orchestration dependencies in runtime path:**
- Risk: `langgraph`, `langchain*`, and `celery` are declared but runtime usage in `backend/app/` is not detected.
- Impact: Increased install time, larger attack surface, and maintenance overhead.
- Migration plan: Remove unused packages from `backend/requirements.txt` or implement actual runtime usage with tests.

**No locked dependency set for backend:**
- Risk: Version ranges (`>=`) can introduce drift between environments.
- Impact: Non-reproducible builds and surprise regressions.
- Migration plan: Introduce lockfile workflow (`pip-tools`/`uv`) and pin production builds.

## Missing Critical Features

**MCP server integration runtime (planned, not implemented):**
- Problem: Universal MCP architecture is documented but backend/frontend MCP modules and endpoints are not present.
- Blocks: Extensible third-party tool ecosystem described in `docs/MCP_INTEGRATION_PLAN.md`.

**Automated test suite:**
- Problem: No project-owned tests for backend APIs/runtime or frontend behavior.
- Blocks: Safe refactoring, release confidence, and regression detection.

**CI pipeline and quality gates:**
- Problem: No repository CI config detected.
- Blocks: Enforced lint/test checks on changes and branch protection automation.

**Production-grade credential/settings management:**
- Problem: Settings UI stores secrets locally and does not persist to backend securely.
- Blocks: Multi-user/admin operations and reliable server-side configuration management.

## Test Coverage Gaps

**Execution engine and tool-call loop:**
- What's not tested: `AgentExecutor` iteration logic, provider fallback, and execution-step persistence.
- Files: `backend/app/runtime/agent_executor.py`, `backend/app/runtime/llm_client.py`.
- Risk: Silent failures or incorrect execution outcomes under provider/tool edge cases.
- Priority: High.

**API contract alignment between frontend/backend:**
- What's not tested: Typed frontend expectations vs actual backend payloads (for example integrations test endpoint).
- Files: `frontend/lib/api.ts`, `backend/app/api/integrations.py`, `backend/app/api/skills.py`.
- Risk: Runtime UI failures despite successful backend responses.
- Priority: High.

**Security-critical behaviors:**
- What's not tested: Auth fail-closed behavior and encryption/decryption paths.
- Files: `backend/app/core/security.py`, `backend/app/core/config.py`.
- Risk: Accidental open access or credential handling regressions.
- Priority: High.

**Scheduling behavior and restart recovery:**
- What's not tested: Cron parsing, schedule registration, and process restart recovery.
- Files: `backend/app/runtime/scheduler.py`, `backend/app/main.py`.
- Risk: Missed executions in production or duplicate scheduling behaviors.
- Priority: Medium.

---

*Concerns audit: 2026-02-08*
