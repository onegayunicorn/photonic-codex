# ResonanceLogs — Event History
**Maturity: PROTOTYPE.** Append-only event log when persistence is enabled.

## Layout
- `store/events.jsonl` — one JSON object per line: `{"seq": N, "prev_hash": "...", "entry_hash": "...", "event": {...sovereign-event-v1 envelope...}}`. Created on first append when `CODEX_PERSISTENT=1`.
- `ai-session.log` — legacy session log (unstructured, not part of the provenance chain).

## Retention
- Default (no env var): process-memory deque bounded by `CODEX_EVENT_LIMIT` (max 1000). `/api/v1/events` reports `durable: false, retention: "process-memory"`.
- With `CODEX_PERSISTENT=1`: append-only JSONL, unbounded. `/api/v1/events` reports `durable: true, retention: "append-only-jsonl"` and includes an `integrity` field from chain verification.

## Read endpoints (v1, read-only)
- `GET /api/v1/events?limit=N` — most recent N events (superseded entries excluded).
- `GET /api/v1/provenance/integrity` — chain verification result; HTTP 500 if status is `TAMPERED` or `GAP` (never healthy).
- `GET /api/v1/provenance/export` — full log with `seq` + `entry_hash` per event (audit export).

No write/delete endpoint is exposed over HTTP. Mutations happen locally via `record_event()` (daemon diagnostics) or `provenance_ctl.py` (operator).
