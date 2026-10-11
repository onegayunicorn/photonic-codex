# Codex Persistent Provenance — drop-in tranche (PR #1 increment)

Status: **PROTOTYPE, tested.** 25/25 tests pass (19 new + 6 original, backwards compatible). Zero new dependencies (stdlib only).

## What this tranche delivers
Priority #1 from the integration plan: durable event storage + integrity hashes + export/rollback.

## Files to add to `photonic-codex` (branch `codex/foundation-runtime-audit`)
| File | Action | Notes |
|---|---|---|
| `provenance_store.py` | ADD | Storage abstraction: `MemoryStore` (default) + `PersistentStore` (JSONL + SHA-256 hash chain), lightweight v1-schema validator |
| `provenance_ctl.py` | ADD | Operator CLI: verify / export / checkpoint / rollback. NOT exposed over HTTP |
| `server.py` | MODIFY | Uses `open_store()`; `record_event()` aligned to shared schema (was emitting invalid `source:"codex-api"` / `classification:"DERIVED"`); adds `/api/v1/provenance/integrity` and `/api/v1/provenance/export` (both read-only) |
| `tests/test_provenance.py` | ADD | 19 tests: persistence-across-reload, tamper/gap detection, invalid-event rejection, export, logical rollback, checkpoint/seal, persistent-mode HTTP |
| `tests/__init__.py` | ADD | Empty — makes tests/ a package for discover |
| `lineage/README.md` | MODIFY | PLANNED → PROTOTYPE; documents seal.json + honesty boundary |
| `ResonanceLogs/README.md` | MODIFY | PLANNED → PROTOTYPE; documents events.jsonl layout + read endpoints |
| `requirements.txt` | UNCHANGED | No new dependencies |

## Enable persistence (opt-in — default unchanged)
```bash
export CODEX_PERSISTENT=1          # default off = in-memory, backwards compatible
export CODEX_DATA_DIR=/path/to/store  # default: ResonanceLogs/store/
python server.py
```

## Operator CLI
```bash
python provenance_ctl.py verify
python provenance_ctl.py export --out audit-export.json
python provenance_ctl.py checkpoint
python provenance_ctl.py rollback --seq 42 --reason "bad ingest batch" --operator alice
```

## Deliberate non-claims (written into code + docs)
- Hash chain = **tamper-evident**, NOT immutable/tamper-proof. `verify()` returns `TAMPERED`/`GAP`; HTTP 500 on those, never healthy.
- Rollback = **logical supersede**, never physical deletion. Physical truncation deferred to `healing/` module with manual approval.
- v1 stays **read-only over HTTP**. No POST/PUT/DELETE endpoints. No commands in payloads (validator rejects them).
- Stale seal = `seal_matches: false`, reported but not conflated with tampering.

## Schema-alignment fix included
`record_event()` previously emitted `source: "codex-api"` and `classification: "DERIVED"`, neither of which exists in `schemas/sovereign-event-v1.schema.json`. Now emits `source: "photonic-codex"`, `classification: "MEASURED"`, with a proper `provenance` block. Events now pass the shared contract validation suite.

## Next tranche unlocked
With durable, integrity-verified event storage in place, **#2 Platform `/capabilities` endpoint** can feed real capability reports that Codex persists with provenance — and **#3 Nexus aggregator** can read both and default to `UNKNOWN` when reports are stale.
