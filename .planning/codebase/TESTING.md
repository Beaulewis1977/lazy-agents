# Testing Patterns

**Analysis Date:** 2026-02-08

## Test Framework

**Runner:**
- pytest (declared in `backend/requirements.txt`; active test files/config not detected).
- Config: Not detected (`pytest.ini`, `pyproject.toml`, `tox.ini`, and `backend/tests/` are not present in source tree).

**Assertion Library:**
- pytest built-in assertions (inferred from `pytest` usage declaration in `backend/requirements.txt`).

**Run Commands:**
```bash
cd backend && pytest                    # Run all backend tests (when tests exist)
cd backend && pytest -q                 # Quiet mode
cd backend && pytest --cov=app          # Coverage for backend app package
```

## Test File Organization

**Location:**
- Not detected in current codebase source directories (`backend/` and `frontend/` contain no project test files outside dependencies).

**Naming:**
- Expected/standard names would be `test_*.py`, `*.test.ts`, `*.spec.tsx`; none detected in project-owned files.

**Structure:**
```text
Not detected: backend/tests/ and frontend test directories are absent.
```

## Test Structure

**Suite Organization:**
```typescript
// Not detected in current codebase.
```

**Patterns:**
- Setup pattern: Not detected.
- Teardown pattern: Not detected.
- Assertion pattern: Not detected.

## Mocking

**Framework:**
- Not detected (no `unittest.mock` usage in dedicated test files, no Jest/Vitest config files).

**Patterns:**
```typescript
// Not detected in current codebase.
```

**What to Mock:**
- For future tests, mock outbound integrations from `backend/app/runtime/llm_client.py` and `backend/app/runtime/skill_executor.py` (OpenAI/Anthropic/Google/GitHub/Slack/Discord HTTP calls).

**What NOT to Mock:**
- Domain models and persistence contracts in `backend/app/models/*.py`; use real schema interactions with isolated test DB where possible.

## Fixtures and Factories

**Test Data:**
```typescript
// Not detected in current codebase.
```

**Location:**
- Not detected (`conftest.py`, fixture modules, and factory modules are absent).

## Coverage

**Requirements:** None enforced (no coverage threshold config detected).

**View Coverage:**
```bash
cd backend && pytest --cov=app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Not detected for backend runtime units (`backend/app/runtime/*.py`) or frontend components/pages (`frontend/app/**/*.tsx`).

**Integration Tests:**
- Not detected for API routes in `backend/app/api/*.py` or DB interactions in `backend/app/core/database.py`.

**E2E Tests:**
- Not used (no Playwright/Cypress config files detected in repository source).

## Common Patterns

**Async Testing:**
```typescript
// Not detected. Backend async code exists in `backend/app/api/*.py` and `backend/app/runtime/*.py`
// but no async test modules are present.
```

**Error Testing:**
```typescript
// Not detected. Exception paths exist (e.g., `HTTPException` branches in `backend/app/api/*.py`)
// but dedicated failure-path tests are absent.
```

---

*Testing analysis: 2026-02-08*
