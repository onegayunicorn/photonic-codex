# Lineage — Provenance Records
**Maturity: PROTOTYPE.** Persistent provenance storage implemented in `provenance_store.py` (opt-in via `CODEX_PERSISTENT=1`).

## What lives here
- `seal.json` — periodic chain-tip checkpoint written by `provenance_ctl.py checkpoint`. Contains `last_seq`, `last_hash`, `count`, `sealed_at`. A stale seal (mismatch against the live log) is reported as `seal_matches: false` by `verify()` — it does **not** indicate tampering by itself.

## Provenance chain
Every persisted event is wrapped as `{seq, prev_hash, entry_hash, event}` in `ResonanceLogs/store/events.jsonl`. `entry_hash = SHA256(canonical_json({seq, prev_hash, event}))`. Genesis `prev_hash = 0*64`.

Minimum metadata per event (from the sovereign envelope): event ID, source system, timestamp, source revision (via `provenance.revision`), classification, evidence references (`provenance.evidence_uri`), and mirror/receipt identity (`correlation_id`). Mirrors never overwrite source evidence.

## Honesty boundary
Hash chaining makes the log **tamper-evident** — `verify()` detects modification (`TAMPERED`) and missing entries (`GAP`). It does **not** make storage immutable or tamper-proof: an attacker with filesystem write access can replace the whole log. Physical deletion protection requires OS/filesystem access controls outside this module. Do not label this ledger immutable.

## Logical rollback
`provenance_ctl.py rollback --seq N --reason "..."` appends an `audit.record` marker with `payload.action = "logical_rollback"`. Entries after seq N are hidden from default queries but **retained physically**; the chain stays verifiable. Physical truncation is intentionally not implemented — use the `healing/` module for operator-controlled restore.
