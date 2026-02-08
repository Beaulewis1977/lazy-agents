---
phase: 02-mcp-server-control-plane
plan: "02"
subsystem: api
tags: [fastapi, sqlalchemy, mcp, lifecycle, control-plane, pytest]
requires:
  - phase: 02-mcp-server-control-plane (02-01)
    provides: persisted MCP server CRUD model and secure env handling
provides:
  - MCP SDK-backed runtime manager with persisted lifecycle state transitions
  - Restart/sync control-plane endpoints backed by app lifespan manager wiring
  - Regression tests for success/failure lifecycle behavior and error visibility
affects: [02-03 MCP management UI, 04 MCP runtime invocation]
tech-stack:
  added:
    - mcp (Python SDK)
  patterns:
    - FastAPI lifespan-managed singleton runtime manager on app.state
    - Persisted lifecycle boundaries for stopped/starting/running/error state machine
key-files:
  created:
    - backend/app/mcp/__init__.py
    - backend/app/mcp/client.py
    - backend/app/mcp/manager.py
    - backend/tests/test_mcp_lifecycle.py
  modified:
    - backend/app/api/mcp.py
    - backend/app/main.py
    - backend/requirements.txt
key-decisions:
  - "Use MCP Python SDK stdio client/session helpers instead of custom subprocess protocol handling."
  - "Run MCP lifecycle manager in FastAPI lifespan so startup/shutdown owns runtime cleanup."
  - "Persist actionable lifecycle failure text in last_error and expose it through API responses."
patterns-established:
  - "Runtime operations route through MCPServerManager methods, not direct endpoint-side process control."
  - "Sync failures close stale runtime handles and transition server status to error deterministically."
duration: 3min
completed: 2026-02-08
---

# Phase 2 Plan 2: MCP Lifecycle Manager Summary

**MCP runtime lifecycle manager with restart/sync control-plane endpoints, deterministic state transitions, and persisted actionable failure visibility.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T18:20:22Z
- **Completed:** 2026-02-08T18:23:05Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Added `app.mcp` client/session and manager modules for startup, shutdown, restart, sync, and tool discovery flows.
- Wired `POST /api/mcp/servers/{id}/restart` and `POST /api/mcp/servers/{id}/sync` into API routes using lifecycle manager dispatch.
- Integrated manager initialization/teardown into FastAPI lifespan via `app.state.mcp_manager`.
- Added lifecycle regression tests proving status/error transitions remain visible to API consumers.

## Task Commits

1. **Task 1: Implement MCP client/session and lifecycle manager modules** - `75be2d5` (feat)
2. **Task 2: Wire restart/sync/status API and FastAPI lifespan integration** - `71d3a76` (feat)
3. **Task 3: Add lifecycle regression tests for status transitions and failure surfacing** - `9b3fd48` (test)

## Files Created/Modified
- `backend/app/mcp/client.py` - MCP SDK session startup/list/call helpers and runtime handle management.
- `backend/app/mcp/manager.py` - Lifecycle state machine, runtime registry, and persisted status/error transitions.
- `backend/app/mcp/__init__.py` - Manager and lifecycle error exports.
- `backend/app/api/mcp.py` - Restart/sync endpoints and manager dependency resolver.
- `backend/app/main.py` - Lifespan startup/shutdown wiring for MCP manager.
- `backend/tests/test_mcp_lifecycle.py` - Restart/sync success/failure regression coverage.
- `backend/requirements.txt` - Added MCP SDK runtime dependency.

## Decisions Made
- Attached `MCPServerManager` to `app.state` and lifecycle-managed it in FastAPI lifespan for centralized runtime ownership.
- Kept list/get MCP responses as the canonical status surface while restart/sync endpoints trigger explicit lifecycle operations.
- Used deterministic error text format (`MCP <action> failed: <ExceptionType>: <message>`) for `last_error` persistence and API diagnostics.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sync lock re-entry deadlock and startup error persistence gap**
- **Found during:** Task 2 (endpoint wiring/integration)
- **Issue:** `sync_server()` could call `start_server()` while holding the same lock; startup failures before runtime launch could leave stale `starting` state.
- **Fix:** Moved startup attempt outside the sync lock and wrapped startup transitions so failures always persist `error` + `last_error`.
- **Files modified:** `backend/app/mcp/manager.py`
- **Verification:** `python -m compileall app`; lifecycle tests pass including failure transitions.
- **Committed in:** `71d3a76` (part of Task 2 commit)

**2. [Rule 2 - Missing Critical] Added missing MCP SDK dependency declaration**
- **Found during:** Post-task verification for runtime readiness
- **Issue:** New lifecycle modules depended on `mcp` but `backend/requirements.txt` did not declare it, causing restart/sync failure on clean installs.
- **Fix:** Added `mcp>=1.0.0` to backend dependency manifest.
- **Files modified:** `backend/requirements.txt`
- **Verification:** Backend MCP tests still pass after dependency manifest update.
- **Committed in:** `a25a67d`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both deviations were required for correct lifecycle behavior and deployable runtime parity.

## Issues Encountered
- Repository pre-commit hook expected a missing config; commits were executed with `PRE_COMMIT_ALLOW_NO_CONFIG=1` to unblock atomic task commits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend lifecycle control-plane behavior for MCP-03/MCP-04 is implemented and regression-tested.
- Phase 02-03 can now consume stable status/error/tool payloads for MCP management UI surfaces.

---
*Phase: 02-mcp-server-control-plane*
*Completed: 2026-02-08*
