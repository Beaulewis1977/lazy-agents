---
phase: 01-security-and-deployment-baseline
plan: "01"
subsystem: auth
tags: [fastapi, api-key, startup-validation, security]
requires: []
provides:
  - "Production startup validation for APP_DEBUG, API_KEY, and SECRET_KEY"
  - "Fail-closed API key authentication outside development mode"
  - "Regression coverage for auth and startup guardrails"
affects: [phase-2-mcp-control-plane, phase-3-agent-ux, deployment]
tech-stack:
  added: []
  patterns:
    - "Fail-fast startup security validation in FastAPI lifespan"
    - "Environment-aware auth: permissive only in explicit development mode"
key-files:
  created:
    - backend/tests/test_auth_fail_closed.py
    - backend/tests/test_startup_validation.py
  modified:
    - backend/app/core/config.py
    - backend/app/core/security.py
    - backend/app/main.py
key-decisions:
  - "Outside development mode, startup fails if API auth or secret hardening is incomplete."
  - "verify_api_key is fail-closed when API auth is not configured in non-development mode."
  - "Auth/startup tests force an async sqlite DATABASE_URL to avoid host env drift during collection."
patterns-established:
  - "Guardrails-before-traffic pattern via startup validation call in lifespan"
  - "Protected router dependency contract asserted by regression tests"
duration: 1min
completed: 2026-02-08
---

# Phase 1 Plan 01: Enforce fail-closed auth and startup validation Summary

**Production startup now enforces secure API/auth configuration and protected routes fail closed with regression coverage.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-08T05:06:15Z
- **Completed:** 2026-02-08T05:06:40Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added non-development startup validation that blocks insecure `APP_DEBUG`, missing `API_KEY`, and weak/default `SECRET_KEY`.
- Updated `verify_api_key` to reject non-development requests when API auth is unconfigured.
- Added focused tests for startup guardrails, auth mode behavior, protected-router wiring, and health/public route behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add production startup security validation** - `848f8b3` (feat)
2. **Task 2: Make API auth fail-closed outside development** - `f9f1f5f` (fix)
3. **Task 3: Add regression tests for auth and startup behavior** - `a481153` (test)

## Files Created/Modified
- `backend/app/core/config.py` - Added production-like security validation helpers and guardrail checks.
- `backend/app/main.py` - Invokes startup validation during lifespan initialization.
- `backend/app/core/security.py` - Enforces fail-closed auth behavior outside development.
- `backend/tests/test_startup_validation.py` - Covers startup validation for env guardrails.
- `backend/tests/test_auth_fail_closed.py` - Covers auth behavior and protected-route/public-health expectations.

## Decisions Made
- Non-development mode is treated as production-like and must satisfy auth/secret baseline before startup.
- Missing API auth config is a 401 condition for protected routes outside development, not permissive behavior.
- Regression tests pin auth/router behavior to prevent future fail-open drift.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Test collection depended on host DATABASE_URL driver**
- **Found during:** Task 3
- **Issue:** Test import path could load a sync PostgreSQL URL (`psycopg2`) and fail async engine creation.
- **Fix:** Forced async sqlite `DATABASE_URL` in test modules before importing app modules.
- **Files modified:** `backend/tests/test_auth_fail_closed.py`, `backend/tests/test_startup_validation.py`
- **Verification:** `PYTHONPATH=. ./venv/bin/pytest -q tests/test_auth_fail_closed.py tests/test_startup_validation.py`
- **Committed in:** `a481153`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Unblocked deterministic test execution without changing production runtime behavior.

## Issues Encountered
- Local git commit hook required `PRE_COMMIT_ALLOW_NO_CONFIG=1` because `.pre-commit-config.yaml` is not present in this branch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Auth baseline for protected APIs is in place for production profile.
- Ready for credential redaction and UI/log masking work in plan `01-02`.

---
*Phase: 01-security-and-deployment-baseline*
*Completed: 2026-02-08*
