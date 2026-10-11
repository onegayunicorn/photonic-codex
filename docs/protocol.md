# Protocol v1

All API responses use UTF-8 JSON unless the route serves the dashboard. Timestamps use UTC ISO-8601 with a trailing `Z`. Unknown fields may be ignored only where the schema explicitly permits them.

## Event envelope

```json
{
  "schema_version": "1.0",
  "event_id": "uuid",
  "timestamp": "2026-10-11T00:00:00Z",
  "source": "codex-api",
  "type": "service.health",
  "classification": "SIMULATED",
  "correlation_id": null,
  "payload": {}
}
```

Allowed evidence classifications: `MEASURED`, `SIMULATED`, `DERIVED`, `UNVERIFIED`. Do not use `MEASURED` without an instrument or source record that can be inspected.

## HTTP routes

- `GET /api/v1/health`: `{ "status": "ok", "service": "photonic-codex", "api_version": "v1" }`
- `GET /api/v1/modules`: `{ "modules": [...] }`
- `GET /api/v1/events?limit=N`: `{ "events": [...], "retention": "process-memory" }`

## Bridge interoperability

A future WebSocket/HTTP bridge adapter must use an allow-listed message type, message-size cap, request ID, replay-resistant authentication, and explicit permission scopes. Unknown message types are rejected. The adapter must not forward raw shell commands, filesystem paths, credentials, or unvalidated payloads.

Transport may be HTTP or WebSocket; protocol semantics should not depend on transport. Remote transport stays disabled until authentication and authorization are implemented and tested.
