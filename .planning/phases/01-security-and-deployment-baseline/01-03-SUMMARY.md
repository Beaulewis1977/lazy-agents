---
phase: 01-security-and-deployment-baseline
plan: "03"
subsystem: infra
tags: [docker-compose, deployment, ops, production]
requires:
  - phase: 01-security-and-deployment-baseline
    provides: "Startup guardrails and secret handling baseline from 01-01/01-02"
provides:
  - "Production compose overlay for single-VM deployment"
  - "Production-safe env contract and startup verification documentation"
  - "Reproducible health/readiness verification steps in docs"
affects: [phase-5-production-hardening, operator-onboarding]
tech-stack:
  added: []
  patterns:
    - "Base compose for development + explicit production overlay"
    - "Fail-fast startup requirements documented as operator contract"
key-files:
  created:
    - compose.production.yaml
  modified:
    - docker-compose.yml
    - frontend/next.config.ts
    - .env.example
    - docs/getting-started.md
    - README.md
key-decisions:
  - "Production deployment uses multi-file compose merge with explicit production overlay."
  - "Production profile uses compose override tags to remove source bind mounts while retaining data persistence mounts."
  - "Setup docs treat APP_ENV/APP_DEBUG/SECRET_KEY/API_KEY as mandatory secure startup inputs."
  - "Worker service is opt-in via compose profile until runtime worker entrypoint exists."
patterns-established:
  - "Single-VM deploy path: compose baseline + production override + health checks"
  - "Operator docs include command-level verification and troubleshooting for security guardrails"
duration: 74min
completed: 2026-02-08
---

# Phase 1 Plan 03: Harden and verify single-VM Compose deployment baseline Summary

**Single-VM production deployment now has an explicit compose overlay, secure env contract, and repeatable health/readiness verification flow.**

## Performance

- **Duration:** 74 min
- **Started:** 2026-02-08T05:18:15Z
- **Completed:** 2026-02-08T06:32:08Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added `compose.production.yaml` to overlay production-specific runtime behavior (no source bind mounts, restart policies, healthchecks).
- Updated `.env.example` and getting-started docs to enforce production-safe startup values and failure-mode expectations.
- Added production startup and `/health` + `/health/ready` verification commands to README and setup docs.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create production Compose overlay and tighten service runtime defaults** - `f8cf25e` (feat)
2. **Task 2: Align env contract with production security baseline** - `23358e1` (docs)
3. **Task 3: Add reproducible baseline verification steps** - `d3fb3e3` (docs)

Additional blocker-fix commits during operational verification:
- `ff296a6` (fix): enable standalone Next.js output for production image
- `b51ae72` (fix): remove Redis host-port binding conflict
- `0e84f60` (fix): pin Next tracing root and make worker service opt-in profile
- `d6147f0` (fix): correct production overlay merge semantics and frontend health check

## Files Created/Modified
- `compose.production.yaml` - Production-only compose overrides for restart, healthchecks, env, and bind-mount removal.
- `docker-compose.yml` - Clarified base compose role and explicit production overlay invocation.
- `frontend/next.config.ts` - Enables stable standalone build output and explicit tracing root.
- `.env.example` - Production-safe defaults and guardrail comments for required startup variables.
- `docs/getting-started.md` - Added production startup path, verification commands, and troubleshooting guidance.
- `README.md` - Added production compose command and health/readiness verification steps.

## Decisions Made
- Production rollout is explicit (`docker-compose.yml` + `compose.production.yaml`) rather than implicit mutation of dev defaults.
- Security startup guardrail variables are treated as required operator inputs in documentation.
- Verification guidance centers on API health/readiness and dashboard reachability.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Frontend image failed at runtime due missing `/app/server.js`**
- **Found during:** Task 1 verification
- **Issue:** Standalone artifact path was inconsistent and production container could not find startup entrypoint.
- **Fix:** Enabled standalone output and pinned tracing/root behavior in `frontend/next.config.ts`.
- **Files modified:** `frontend/next.config.ts`
- **Verification:** `npm run build` + `docker compose ... up -d --build` + `curl -I http://localhost:3000`
- **Committed in:** `ff296a6`, `0e84f60`

**2. [Rule 3 - Blocking] Redis host port conflict prevented stack startup**
- **Found during:** Task 1 verification
- **Issue:** Host port `6379` was already allocated, causing compose startup failure.
- **Fix:** Removed Redis host port exposure from base compose and kept service internal-only.
- **Files modified:** `docker-compose.yml`
- **Verification:** `docker compose ... up -d` succeeded for Redis/API/frontend stack.
- **Committed in:** `b51ae72`

**3. [Rule 3 - Blocking] Production overlay inherited development bind mounts**
- **Found during:** Task 1 verification
- **Issue:** Development bind mounts shadowed image artifacts in production profile, reintroducing runtime startup failures.
- **Fix:** Used compose override tags to reset inherited volumes and reapply only required data mounts.
- **Files modified:** `compose.production.yaml`
- **Verification:** `docker compose ... config` confirmed merged volumes; production stack reached healthy state.
- **Committed in:** `d6147f0`

**4. [Rule 3 - Blocking] Worker default command referenced missing module**
- **Found during:** Task 1 verification
- **Issue:** `python -m app.worker` does not exist, causing restart loops.
- **Fix:** Made worker service opt-in via `worker` profile so default production startup remains stable.
- **Files modified:** `docker-compose.yml`
- **Verification:** `docker compose ... ps` shows healthy default services without worker crash loops.
- **Committed in:** `0e84f60`

---

**Total deviations:** 4 auto-fixed (4 blocking)
**Impact on plan:** All fixes were required to make production-profile startup reproducible and healthy on real Docker hosts.

## Issues Encountered
- None remaining after blocker fixes; production profile now boots and passes health/readiness checks.

## User Setup Required

None - no additional external service setup beyond documented `.env` values.

## Next Phase Readiness
- Phase 1 deployment baseline is documented and production-oriented.
- Phase verification can now validate SEC/OPS must-haves against code and docs.

---
*Phase: 01-security-and-deployment-baseline*
*Completed: 2026-02-08*
