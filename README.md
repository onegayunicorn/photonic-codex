# Photonic Codex

**A local-first, modular personal computing environment with explicit trust boundaries, observable services, and auditable state.**

Photonic Codex combines a browser dashboard, local API, optional background workers, structured event history, and adapters for other Sovereign systems. It is intended for desktop Linux, Windows/PowerShell, and Android/Termux where dependencies are supported.

> **Status:** Early development. Integrations and quantum/photonic terminology remain conceptual unless supported by reproducible tests and evidence. This repository does not establish physical quantum hardware or photonic execution.

## Principles

- **Local-first:** data remains on the host by default; remote connectivity is opt-in.
- **Read-only by default:** integrations report state before any write capability is considered.
- **Fail closed:** missing authentication, configuration, or safety checks deny privileged operations.
- **Evidence before claims:** use the shared labels `PROPOSED`, `SIMULATED`, `DEMONSTRATED`, `MEASURED`, `UNVERIFIED`, and `VALIDATED`.
- **Modular contracts:** directories are organizational boundaries; communication uses documented interfaces.
- **No arbitrary execution endpoint:** the HTTP API does not accept shell commands or arbitrary script bodies.
- **Portable operations:** configuration is environment-driven and secrets are never committed.

## Ecosystem architecture

```text
Photonic Codex             Unicorn Sovereign Platform        Quantum Multiversal Nexus
Local operations           Runtime and capability evidence   Manifests and status display
Events / provenance  <-->  Versioned read-only reports  <--> Read-only mirrors
          \\________________ Shared event contract v1 ________________//
```

Repositories remain separate and authoritative for their own state. Cross-repository connectivity is not established merely by sharing documentation.

### Repository responsibilities

| Domain | Intended responsibility |
|---|---|
| `Brain/`, `Portals/` | Coordination contracts and UI/API entry points |
| `ShrineNodes/`, `sandbox/` | Named execution contexts and controlled experiments |
| `ResonanceLogs/`, `lineage/`, `logs/` | Event history, provenance, and operational diagnostics |
| `quantum-doors/`, `healing/` | State-transition policy and documented recovery plans |
| `network/`, `orbital/`, `tesla-tower/`, `echo/`, `whisper/` | Future transport/topology adapters; disabled until configured |
| `meta-hub.html`, `meta-hub/` | Dashboard and view models |
| `onboarding/`, `git/` | Setup checks and read-only Git metadata |

Directory names are not proof of implementation. See the module registry and assign maturity based on tests.

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

The API binds to `127.0.0.1:7070` by default. Open `http://127.0.0.1:7070/`. Set `CODEX_PORT` to change the port. Remote binding requires explicit configuration and a separate security review.

## API v1

- `GET /` — dashboard
- `GET /api/v1/health` — service liveness metadata
- `GET /api/v1/modules` — module registry and maturity labels
- `GET /api/v1/events?limit=50` — bounded in-memory event view, not durable storage

No endpoint runs shell commands or triggers external writes. The current event buffer is not a durable or tamper-proof audit ledger.

## Shared protocol and ecosystem links

- [Sovereign Event Contract v1](docs/protocol.md)
- [Architecture and module boundaries](docs/architecture.md)
- [Security policy](SECURITY.md)
- [Unicorn Sovereign Platform](https://github.com/onegayunicorn/unicorn-sovereign-platform)
- [Quantum Multiversal Nexus](https://github.com/onegayunicorn/quantum-multiversal-nexus)

## Validation

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

CI is configured for Python compilation and unit tests. A configured workflow is not evidence of passing checks; inspect the actual run result.

## Security gates

1. Bind to loopback by default.
2. Store credentials outside source control.
3. Require authentication and authorization before remote access.
4. Validate payloads and cap sizes.
5. Keep external writes disabled until a dedicated adapter has tests and explicit approval.
6. Preserve source evidence labels and provenance.
7. Do not assert hardware attestation without independently inspectable evidence.
