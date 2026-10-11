# Photonic Codex

**A local-first, modular personal computing environment with explicit trust boundaries, observable services, and auditable state.**

Photonic Codex brings together a browser dashboard, local API, optional background workers, structured event history, and adapters for other Sovereign systems. The project is designed to run on desktop Linux, Windows/PowerShell, and Android/Termux where its dependencies are available.

> **Status:** Early development. Treat integrations and quantum/photonic terminology as conceptual unless a capability is backed by reproducible tests and measured evidence. This repository does not establish physical quantum hardware or photonic execution.

## Principles

- **Local-first:** data remains on the host by default; remote connectivity is opt-in.
- **Read-only by default:** integrations report state before they are allowed to change anything.
- **Fail closed:** unavailable authentication, configuration, or safety checks deny privileged operations.
- **Evidence before claims:** label results as `MEASURED`, `SIMULATED`, `DERIVED`, or `UNVERIFIED`.
- **Modular contracts:** directories are organizational boundaries; communication happens through documented interfaces, not implicit folder coupling.
- **No arbitrary execution endpoint:** the HTTP API never accepts shell commands or arbitrary script bodies.
- **Portable operations:** configuration is environment-driven and secrets are never committed.

## Initial architecture

```text
Browser dashboard (meta-hub.html)
          | same-origin HTTP / JSON
          v
Local API (server.py) ----> Module registry
          |                Event/provenance ledger
          +----> Optional adapters (disabled until configured)
                          |
                    Sovereign / B2D bridge
                    (explicit opt-in only)
```

### Directory domains

| Directory | Intended responsibility |
|---|---|
| `Brain/` | Coordination contracts and decision metadata; no unrestricted execution |
| `Portals/` | UI and API entry-point adapters |
| `ShrineNodes/` | Named local execution contexts with explicit trust labels |
| `ResonanceLogs/` | Append-oriented application events |
| `quantum-doors/` | State-transition policy and gate definitions; not physical quantum claims |
| `meta-hub/` | Dashboard support assets and view models |
| `mythic/`, `emotions/`, `epic/` | Optional symbolic/narrative metadata, separated from security decisions |
| `orbital/`, `tesla-tower/`, `network/`, `echo/`, `whisper/` | Transport and topology adapters; network access remains disabled unless configured |
| `lineage/` | Provenance records and integrity metadata |
| `healing/` | Recovery plans and rollback *descriptions*; no automatic privileged rollback |
| `sandbox/` | Isolated experiments and deterministic fixtures |
| `onboarding/` | Setup checks and first-run guidance |
| `git/` | Git status/metadata adapters; no implicit pushes |
| `logs/` | Operational logs, separate from provenance records |

These names are proposed responsibilities, not proof that each module is implemented. Each module must document its maturity and public interface.

## Quick start

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Linux / macOS / Termux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py
```

The API binds to `127.0.0.1:7070` by default. Open `http://127.0.0.1:7070/`. To change the port, set `CODEX_PORT`. Remote binding requires an explicit `CODEX_HOST` override and should only be done behind an authenticated, appropriately configured network boundary.

## API v1

- `GET /` — dashboard shell
- `GET /api/v1/health` — liveness and versioned service metadata
- `GET /api/v1/modules` — static module registry and implementation status
- `GET /api/v1/events?limit=50` — bounded in-memory event view (not durable storage)

No endpoint runs shell commands, loads arbitrary Python, or triggers external writes. The in-memory event list is a development baseline, not a durable audit ledger.

## Validation

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Runtime scripts

PowerShell daemon/agent scripts must support `-WhatIf` or a dry-run equivalent, structured logs, bounded retries, and graceful shutdown before they are treated as service-grade. Do not run unreviewed scripts with administrator/root privileges.

## Security and integration gates

1. Bind to loopback by default.
2. Keep credentials in environment variables or a secret manager, never in the repository.
3. Require authentication and authorization before enabling non-loopback access.
4. Validate request schemas and cap payloads.
5. Apply timeouts, rate limits, and bounded log/event retention.
6. Keep integration writes disabled until a specific adapter has tests and explicit configuration.
7. Label all simulated or inferred results; do not imply hardware attestation without evidence.
8. Preserve Git history; use branches and pull requests instead of force pushes.

See [docs/architecture.md](docs/architecture.md), [docs/protocol.md](docs/protocol.md), and [SECURITY.md](SECURITY.md).
