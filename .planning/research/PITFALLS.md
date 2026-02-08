# Pitfalls Research

**Domain:** Self-hosted AI agent control plane with MCP runtime expansion
**Researched:** 2026-02-08
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Auth Optional in Real Deployments

**What goes wrong:** API routes are reachable without enforced auth in production-like environments.

**Why it happens:** Development defaults leak into deployment defaults.

**How to avoid:** Fail closed outside development profile; validate required auth config at startup.

**Warning signs:** Empty/missing API key in deployed environment; public route access succeeds unexpectedly.

**Phase to address:** Foundation hardening phase.

---

### Pitfall 2: Secret Leakage Through UI/Logs/Responses

**What goes wrong:** Credentials appear in frontend storage, API responses, or execution logs.

**Why it happens:** Convenience shortcuts in settings forms and debug output.

**How to avoid:** Server-side encrypted storage only, masked UI fields, structured redaction in all logging paths.

**Warning signs:** Tokens visible in browser devtools/localStorage, plaintext secrets in logs, or secret fields returned in API payloads.

**Phase to address:** Security baseline + integration settings phase.

---

### Pitfall 3: Unmanaged MCP Process Lifecycle

**What goes wrong:** Orphaned subprocesses, stale sessions, restart loops, and false "running" states.

**Why it happens:** No single lifecycle owner and weak health/retry policy.

**How to avoid:** Central manager with explicit state machine (`stopped/starting/running/error`), bounded retries, and sync checkpoints.

**Warning signs:** Frequent manual restarts, drift between UI status and actual process state, zombie processes.

**Phase to address:** MCP runtime foundation phase.

---

### Pitfall 4: Tool Namespace Collisions and Stale Discovery

**What goes wrong:** Wrong tool invoked, duplicate names across servers, or outdated schemas causing execution failures.

**Why it happens:** Dynamic tool registration without canonical namespacing or cache invalidation.

**How to avoid:** Enforce canonical IDs (`mcp::{server}::{tool}`), version/hash tool schema snapshots, and force-sync command.

**Warning signs:** Intermittent tool-not-found or schema mismatch errors after server updates.

**Phase to address:** MCP registry + routing phase.

---

### Pitfall 5: Contract Drift Between Frontend and Backend

**What goes wrong:** UI assumes response shape different from API, causing silent operational failures.

**Why it happens:** No shared contract tests and ad-hoc response evolution.

**How to avoid:** Typed API contracts + endpoint contract tests + CI gate for schema compatibility.

**Warning signs:** UI "test connection" shows false failures despite backend success; runtime parsing errors.

**Phase to address:** Stabilization and verification phase.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Handle MCP inside existing monolithic executor only | Fast first implementation | Hard-to-maintain runtime and higher regression risk | Only temporary behind clear refactor deadline |
| Skip tool schema validation | Faster onboarding | Runtime failures and unsafe calls | Never in production-ready path |
| Store settings secrets in browser for convenience | Quick UI implementation | High credential exposure risk | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| MCP stdio servers | Assume process alive == protocol ready | Require initialize handshake and capability check |
| MCP HTTP servers | Treat transport as trusted without auth strategy | Use explicit auth model and endpoint validation |
| Native integrations + MCP | Mix naming and routing conventions | Canonical namespacing and one resolver path |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-discover tools on every call | High latency and noisy server load | Cache discovery with explicit sync/refresh | Moderate usage (dozens of calls/min) |
| Unbounded websocket log fanout | API CPU/memory spikes | Bounded queues and backpressure | Multi-user concurrent monitoring |
| Serial blocking MCP calls in long loops | Slow end-to-end runs | Timeout budgets + async concurrency where safe | Complex workflows with many tool calls |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Production starts without enforced auth | Unauthorized access | Fail-closed startup checks and required auth config |
| Secrets sent back in API payloads | Credential compromise | Explicit response models excluding secret fields |
| Over-scoped tool execution by default | Excessive blast radius | Minimize default permissions and explicit mapping |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Opaque "server error" statuses | Users cannot self-recover | Actionable status messages and recommended remediation |
| No distinction between config saved and server running | Confusion and support churn | Separate persistence state from runtime health state |
| Hidden tool schemas | Hard to debug incorrect parameters | Tool browser with required/optional args and examples |

## "Looks Done But Isn't" Checklist

- [ ] **MCP Server Added:** verify tool list is discoverable and cached, not just config saved.
- [ ] **Tool Invocation Works:** verify end-to-end from agent loop, not only manual test call.
- [ ] **Security Baseline:** verify no secrets in responses/logs/localStorage.
- [ ] **Production Mode:** verify auth cannot be bypassed by missing env defaults.
- [ ] **Installability:** verify clean VM + Compose can reach first successful run.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Auth optional in deployment | HIGH | Enforce startup guard, rotate exposed keys, re-validate all public endpoints |
| Secret leakage | HIGH | Revoke/rotate credentials, purge logs/storage, patch redaction/storage flows |
| MCP lifecycle instability | MEDIUM | Kill orphan sessions, deploy manager state machine fix, add health probes |
| Namespace collisions | MEDIUM | Rebuild registry with canonical IDs, migrate existing references |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Auth optional in prod | Security foundation | Deployed env rejects unauthenticated protected routes |
| Secret leakage paths | Security + integrations | Automated checks show no secret fields in responses/logs |
| MCP lifecycle instability | MCP runtime core | Restart/sync tests pass with stable state transitions |
| Namespace/schema drift | MCP registry/routing | Tool discovery cache consistency and call contract tests pass |
| Frontend/backend drift | Stabilization | Contract tests and UI integration tests pass |

## Sources

- Context7 `/modelcontextprotocol/python-sdk` — lifecycle and tool-call patterns
- https://modelcontextprotocol.io/docs/learn/architecture — architecture and transport details
- https://modelcontextprotocol.io/specification/2025-03-26/architecture — isolation/security model
- https://owasp.org/www-project-top-10-for-large-language-model-applications/ — LLM app risk framing
- `.planning/codebase/CONCERNS.md` — current project-specific risk evidence
- Context7 `/fastapi/fastapi` and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ — auth/security implementation patterns

---
*Pitfalls research for: self-hosted AI agent control plane with MCP expansion*
*Researched: 2026-02-08*
