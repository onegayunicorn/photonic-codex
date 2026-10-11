# Architecture and module boundaries

## Runtime components

1. **Presentation** — `meta-hub.html` renders state and issues same-origin, read-only API requests.
2. **HTTP service** — `server.py` exposes versioned health, module inventory, and event-read endpoints.
3. **Module registry** — a static, reviewed list describing ownership and implementation maturity. Directory names alone do not imply executable capability.
4. **Event buffer** — bounded, process-local diagnostics. This is not durable storage and must not be described as a tamper-proof ledger.
5. **Adapters** — external network, Git, device, or B2D connectors. Disabled until independently configured and tested.
6. **PowerShell lifecycle scripts** — startup/worker/daemon responsibilities must be explicit and observable; no automatic elevation.

## Trust zones

- **Zone 0 — UI:** untrusted input; no secrets; no direct privileged operations.
- **Zone 1 — Local API:** loopback-bound; validates requests; exposes read-only state.
- **Zone 2 — Local modules:** explicit interfaces, bounded inputs, least privilege.
- **Zone 3 — External adapters:** off by default; separate credentials, authentication, authorization, timeouts, and audit records.
- **Zone 4 — Hardware or privileged actions:** HOLD until hardware identity, operator authorization, interlocks, tests, and rollback/stop behavior are independently verified.

A higher zone must never be reached solely because a UI flag or narrative state says a system is trusted.

## Module maturity labels

- `PLANNED`: documented intent only.
- `SKELETON`: files exist but useful behavior is not implemented.
- `SIMULATED`: deterministic or synthetic behavior, no physical-device claim.
- `IMPLEMENTED`: behavior exists with unit tests.
- `VERIFIED`: tests and reproducible evidence cover the stated claim.
- `HOLD`: gated due to missing evidence or safety prerequisites.

Do not mark a module `VERIFIED` based only on a successful process start.

## Configuration

- `CODEX_HOST`: defaults to `127.0.0.1`; remote binding requires an explicit override and security review.
- `CODEX_PORT`: defaults to `7070`.
- `CODEX_EVENT_LIMIT`: bounded in-memory event capacity, defaults to `200`.

No credentials or remote bridge URLs are hard-coded. New integrations should define a separate configuration contract and remain disabled by default.

## Failure handling

- Invalid input receives a 4xx response with a stable error code.
- Unexpected errors are logged server-side and return a generic 500 response.
- Health reports process availability, not correctness of external dependencies.
- Shutdown should stop accepting work and flush only those records whose persistence has been explicitly configured.
