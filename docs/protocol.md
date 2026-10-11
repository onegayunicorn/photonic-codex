# Sovereign Ecosystem Event Contract v1

Status: PROPOSED CONTRACT — integration implementation and interoperability tests are pending.

This is the canonical shared event shape for Photonic Codex, Unicorn Sovereign Platform, and Quantum Multiversal Nexus. Each repository remains authoritative for its own state. Consumers must not upgrade another system's evidence classification or infer health from stale or missing reports.

## Event envelope

```json
{
  "schema_version": "1.0",
  "event_id": "UUID",
  "timestamp": "2026-10-11T00:00:00Z",
  "source": "unicorn-sovereign-platform",
  "type": "capability.report",
  "classification": "SIMULATED",
  "correlation_id": null,
  "provenance": {
    "repository": "onegayunicorn/unicorn-sovereign-platform",
    "revision": "git-commit-sha",
    "evidence_uri": null
  },
  "payload": {}
}
```

Required fields: `schema_version`, `event_id`, `timestamp`, `source`, `type`, `classification`, and `payload`. Capability and test-result claims must include provenance. Timestamps must be UTC ISO-8601 with trailing `Z`. Payloads must be bounded JSON objects and must never include credentials or arbitrary commands.

## Canonical evidence labels

- `PROPOSED`: intended or planned, not implementation evidence.
- `SIMULATED`: model, stub, fixture, emulator, or synthetic result.
- `DEMONSTRATED`: behavior observed in a reproducible test or controlled demonstration; scope and environment must be recorded.
- `MEASURED`: raw observation from an identified instrument/source with procedure, units, timestamp, and calibration context where relevant.
- `UNVERIFIED`: reported but not independently substantiated.
- `VALIDATED`: a named acceptance criterion passed with recorded test/evidence references; this does not imply broader production readiness.

Do not silently translate labels. Preserve unknown source labels verbatim and flag them as unmapped. A test report is not automatically evidence of physical quantum operation.

## Health values

Allowed health values: `HEALTHY`, `DEGRADED`, `UNAVAILABLE`, `UNKNOWN`. Missing responses, stale reports, invalid signatures, and schema errors must never be treated as healthy. Health observations should include observation time and source revision where available.

## Transport and permission boundary

- Phase 1: local fixtures and read-only JSON.
- Phase 2: authenticated read-only HTTP polling; WebSocket only after auth, authorization, message caps, reconnect, and replay controls are tested.
- v1 does not authorize command execution, deployment, rollback, Git push, or hardware control.
- Any future write protocol requires a new version, named permission scopes, explicit operator approval, idempotency, audit records, and tested failure/rollback behavior.

## Provenance and compatibility

Mirrors preserve the original event ID, classification, timestamp, source, and provenance. Consumers may add a local receipt event but must not rewrite source evidence. Hash chaining alone does not make storage immutable or tamper-proof.

Producers publish schema versions and contract tests. Consumers reject unsupported major versions and invalid required fields. Breaking changes require a new major version.

## Integration status

This contract is proposed. Do not claim that the three repositories are connected until producer/consumer contract tests and live read-only integration tests pass.
