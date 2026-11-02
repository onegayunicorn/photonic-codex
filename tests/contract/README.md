# Sovereign Ecosystem — Contract Validation Suite (event v1)

Status: **PROPOSED CONTRACT** — this suite validates the shared event envelope.
It does **not** prove live interoperability; that requires Phase 2 read-only
integration tests (see `docs/protocol.md` in each repository).

This is the first executable tranche beyond documentation: schema-validation
tests + representative event fixtures, designed to be dropped unchanged into
`photonic-codex`, `unicorn-sovereign-platform`, and `quantum-multiversal-nexus`
(or the future `sovereign-root` coordination workspace).

## Layout

```
sovereign-contract-tests/
├── schemas/sovereign-event-v1.schema.json   # canonical shared schema (identical in all 3 repos)
├── fixtures/
│   ├── valid/             (8)  must pass schema + semantic checks
│   ├── invalid-schema/    (12) must FAIL JSON Schema validation — one fault each
│   └── invalid-semantic/  (6)  pass schema but FAIL protocol semantic rules
├── validate.py                  # schema + semantic validator, exit non-zero on failure
├── gen_fixtures.py              # regenerate fixtures from source dicts
└── ci-example.yml               # GitHub Actions workflow snippet
```

## Run

```bash
pip install jsonschema rfc3339-validator
python3 validate.py          # full suite — 26 passed, 0 failed expected
python3 validate.py path/to/event.json   # validate a single event file
```

## What is enforced

**JSON Schema (draft 2020-12):** required fields, `schema_version` const `1.0`,
UTC timestamp with trailing `Z`, enumerated `source` / `type` / `classification`,
`additionalProperties: false` on envelope and provenance, bounded payload.

**Semantic (protocol.md rules the schema cannot express):**
1. `capability.report` and `test.result` **must include provenance** with a
   non-empty `repository`.
2. `service.health` payload `health` must be one of `HEALTHY / DEGRADED /
   UNAVAILABLE / UNKNOWN` — missing/stale/invalid is never healthy.
3. Payload keys matching credential patterns (`password`, `secret`, `token`,
   `api_key`, `private_key`, …) are rejected.
4. Payload keys naming write/command actions (`command`, `execute`, `script`,
   `deploy`, `rollback`, `git_push`, …) are rejected — v1 authorizes read-only
   events only.

## Negative-fixture catalogue (one fault each)

| # | invalid-schema | fault |
|---|---|---|
| 01 | missing-required-event-id | required field dropped |
| 02 | wrong-schema-version | `schema_version: "2.0"` |
| 03 | timestamp-no-trailing-z | `+00:00` instead of `Z` |
| 04 | timestamp-malformed | not a date-time |
| 05 | unknown-source | fourth source identity |
| 06 | unknown-type-command | `system.command` (v1 forbids) |
| 07 | unknown-classification | `OPERATIONAL` |
| 08 | extra-top-level-property | `additionalProperties:false` |
| 09 | payload-not-object | payload is a string |
| 10 | event-id-too-long | 129 chars > max 128 |
| 11 | provenance-extra-property | provenance `additionalProperties:false` |
| 12 | correlation-id-wrong-type | number instead of string\|null |

| # | invalid-semantic | fault |
|---|---|---|
| 01 | capability-without-provenance | schema-valid, protocol requires provenance |
| 02 | test-result-without-provenance | same |
| 03 | capability-empty-repository | `repository: ""` |
| 04 | health-value-not-allowed | `RUNNING_FINE` |
| 05 | payload-contains-command | `command` key — v1 read-only |
| 06 | payload-contains-credential | `api_secret` key — forbidden |

## Wiring into CI

Copy `ci-example.yml` to `.github/workflows/contract-tests.yml` in any repo.
The suite is repo-agnostic: it only needs the schema + fixtures, so each repo
can vendor the same copy and fail independently on contract drift.

**Drift detection:** if any repo modifies `schemas/sovereign-event-v1.schema.json`
locally, the fixtures will fail — exactly the intended signal that a contract
change needs a new major version and cross-repo alignment.

## Not covered (later phases, by design)

- Live HTTP/WebSocket interoperability, auth, replay controls (Phase 2).
- Coordinated operations / single `activate.sh` (Phase 3).
- Hash-chain immutability claims — protocol.md explicitly notes hashing alone
  does not prove tamper-proof storage.
