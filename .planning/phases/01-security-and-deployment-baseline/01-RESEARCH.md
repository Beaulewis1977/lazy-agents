# Phase 01: Security and Deployment Baseline - Research

**Researched:** 2026-02-08
**Domain:** FastAPI security posture, secret handling, and single-VM Docker Compose operability
**Confidence:** HIGH

## Summary

This phase should lock in a fail-closed security baseline and production-safe deployment profile before any MCP expansion work. In the current codebase, protected API routes are only enforced when `API_KEY` is set, encryption key derivation is weak (`SECRET_KEY` truncation/padding), and deployment defaults still include development-oriented bind mounts and debug posture.

The standard approach is: enforce auth requirement outside development at dependency/startup boundaries, use a proper KDF for secret-encryption key material (with persisted salt), and split development vs production Compose settings so production disables mutable code mounts and applies restart/health policies.

For this repository specifically, planning should target three execution units: (1) fail-closed auth + startup guards, (2) cross-surface secret masking/redaction, and (3) Compose hardening + first-run verification.

**Primary recommendation:** Implement a production profile that refuses to boot with insecure auth/secret settings, redacts sensitive fields in API/logs, and runs from immutable images under a production Compose overlay.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `>=0.109` (project) / current docs track 0.12x | API auth dependencies and startup validation hooks | Router/app dependency model makes fail-closed auth enforcement explicit and testable |
| cryptography (`Fernet` + KDF primitives) | `>=42` (project) | Secret encryption at rest | Official docs define password-based key derivation for Fernet keys via PBKDF2HMAC/Scrypt |
| Docker Compose | v2 line | Single-VM deployment target | Official docs provide production override pattern and restart/operability guidance |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | `>=2.1` | Typed startup config validation | Enforce required env vars in non-development mode |
| structlog | `>=24.1` | Structured logging | Centralized redaction of sensitive fields before emission |
| httpx | `>=0.26` | Outbound integration checks | Ensure token-bearing requests never log plaintext headers/body |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| API key header auth baseline | OAuth2/JWT stack | More complete identity model, but unnecessary scope for Phase 1 baseline requirement |
| Fernet key from KDF | External KMS/HSM | Stronger enterprise posture, but out-of-scope for single-VM v1 |
| Single Compose file for all envs | `compose.yaml` + `compose.production.yaml` | Slightly more config maintenance, but cleaner and safer production defaults |

**Installation:**
```bash
pip install "fastapi>=0.109" "cryptography>=42" "pydantic-settings>=2.1" "structlog>=24.1"
```

## Architecture Patterns

### Recommended Project Structure
```text
backend/app/
├── core/
│   ├── config.py        # startup security guardrails
│   └── security.py      # auth dependency + encryption/redaction helpers
├── api/
│   ├── __init__.py
│   ├── integrations.py  # secret-safe payloads
│   └── ...
└── runtime/
    └── agent_executor.py # log redaction boundaries

# deployment
compose.yaml
compose.production.yaml
```

### Pattern 1: Fail-Closed Auth Boundary
**What:** In non-development mode, missing/invalid credentials return 401 for protected routes and insecure config prevents startup.
**When to use:** All operational API routers.
**Example:**
```python
# Source: Context7 /fastapi/fastapi (router dependencies + dependency exceptions)
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(dependencies=[Depends(verify_api_key)])

def verify_api_key(...):
    if production_mode and not configured_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
```

### Pattern 2: KDF-Derived Encryption Key
**What:** Derive Fernet key material using PBKDF2HMAC or Scrypt with stored salt.
**When to use:** Encrypt/decrypt integration credentials and server-side secrets.
**Example:**
```python
# Source: Context7 /pyca/cryptography (fernet + PBKDF2HMAC guidance)
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=1_200_000)
key = base64.urlsafe_b64encode(kdf.derive(secret_bytes))
```

### Pattern 3: Production Compose Overlay
**What:** Keep base Compose for local dev; overlay production-specific security/operability settings.
**When to use:** Single-VM deployment.
**Example:**
```yaml
# Source: docs.docker.com/compose/how-tos/production/
services:
  api:
    restart: unless-stopped
    # no source bind mount in production
```

### Anti-Patterns to Avoid
- **Auth by omission:** Allowing request access because `API_KEY` is unset in non-dev environments.
- **Ad-hoc key derivation:** Truncating/padding `SECRET_KEY` into Fernet key material.
- **Secret persistence in browser localStorage:** Treating browser state as canonical secret storage.
- **One-size-fits-all Compose:** Using dev bind mounts/debug settings in production deployment.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API auth gate | Custom middleware parsing raw headers across routes | FastAPI dependency injection (`Depends`/`Security`) at router or include_router boundary | Consistent enforcement and explicit contract |
| Secret key derivation | Manual byte slicing/padding tricks | `PBKDF2HMAC` or `Scrypt` from `cryptography` | Correct entropy stretching and brute-force resistance |
| Production/development env switching | Inline conditionals in many services | Compose override files and env-based settings model | Lower drift and repeatable deployments |
| Redaction in each endpoint | Per-route ad-hoc masking logic | Centralized redaction helper used in response shaping + logging | Prevents missed leakage paths |

**Key insight:** Security bugs in this phase mostly come from “shortcut glue code.” Use framework/library primitives and centralize enforcement.

## Common Pitfalls

### Pitfall 1: Production starts with permissive auth
**What goes wrong:** Protected routes accept requests when `API_KEY` is absent.
**Why it happens:** Current auth dependency treats missing key as development behavior globally.
**How to avoid:** Add startup validation and dependency behavior tied to `APP_ENV`.
**Warning signs:** `APP_ENV=production` with empty `API_KEY`, but API still accessible.

### Pitfall 2: Weak encryption key material
**What goes wrong:** Secret encryption can be weakened by deterministic truncation/padding.
**Why it happens:** Fernet key format requirements are met syntactically but not with proper KDF semantics.
**How to avoid:** Use PBKDF2HMAC/Scrypt + stored salt and iteration/cost parameters.
**Warning signs:** No salt in config/storage; direct `SECRET_KEY` byte manipulation.

### Pitfall 3: Token leakage in logs/steps
**What goes wrong:** API keys/tokens appear in log messages or execution payloads.
**Why it happens:** Raw request/response values are persisted or emitted without redaction.
**How to avoid:** Redaction middleware/helper for known sensitive keys and header names before persistence/logging.
**Warning signs:** `api_key`, `token`, `secret` values visible in `Execution.input_data`, logs, or websocket streams.

### Pitfall 4: Dev Compose config promoted to production
**What goes wrong:** Production container behavior depends on host-mounted source and debug defaults.
**Why it happens:** Single compose file optimized for development convenience.
**How to avoid:** Add production overlay (restart policy, immutable code in image, prod env vars).
**Warning signs:** `./backend:/app` and `APP_DEBUG=true` in deployed profile.

## Code Examples

Verified patterns from official sources:

### Router-level dependency enforcement
```python
# Source: Context7 /fastapi/fastapi
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/agents", dependencies=[Depends(verify_api_key)])
```

### PBKDF2-derived Fernet key
```python
# Source: Context7 /pyca/cryptography
import os, base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

salt = os.urandom(16)
key = base64.urlsafe_b64encode(
    PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=1_200_000).derive(secret)
)
```

### Compose production override invocation
```bash
# Source: Docker Compose production docs
docker compose -f compose.yaml -f compose.production.yaml up -d
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Implicitly open API unless key configured | Environment-aware fail-closed policy for non-dev | Established best practice, reinforced in modern FastAPI deployment guidance | Prevents accidental public exposure |
| Simple “secret string -> encryption key” transforms | KDF-based derivation (PBKDF2/Scrypt) with salt | Current cryptography guidance | Stronger resistance against offline guessing |
| Single Compose config for all environments | Base + production override files | Current Docker Compose production guidance | Safer deploy defaults and lower drift |

**Deprecated/outdated:**
- “Store provider credentials in localStorage for convenience”: unsafe for production profile and incompatible with SEC-02/SEC-03 goals.

## Open Questions

1. **API auth model scope for Phase 1**
   - What we know: Requirement only mandates unauthenticated rejection in non-development mode.
   - What's unclear: Whether Phase 1 should keep API-key-only or introduce JWT/session identity now.
   - Recommendation: Keep API key baseline in Phase 1; defer identity expansion to later phase.

2. **Secret migration strategy**
   - What we know: Existing encrypted rows use current derivation.
   - What's unclear: Need for backfill/rotation when moving to KDF+salt format.
   - Recommendation: Include compatibility reader + migration task in this phase plan.

## Sources

### Primary (HIGH confidence)
- Context7 `/fastapi/fastapi` - router dependencies, dependency-enforced auth patterns
- Context7 `/pyca/cryptography` - Fernet key derivation guidance with PBKDF2HMAC/Scrypt
- Docker docs: https://docs.docker.com/compose/how-tos/production/ - production Compose overlays and restart guidance

### Secondary (MEDIUM confidence)
- `.planning/codebase/CONCERNS.md` - project-specific security/deployment risk inventory
- `.planning/codebase/ARCHITECTURE.md` - current backend/frontend boundary and runtime behavior

### Tertiary (LOW confidence)
- Perplexity ecosystem discovery for Compose production patterns (used only for discovery, verified against official Docker docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - based on current official docs and project constraints
- Architecture: HIGH - matches existing codebase boundaries and phase requirement mapping
- Pitfalls: HIGH - observed in current code and aligned with documented practices

**Research date:** 2026-02-08
**Valid until:** 2026-03-10
