#!/usr/bin/env python3
"""Generate sovereign-event-v1 contract fixtures.

Produces three categories under fixtures/:
  valid/            - must pass schema validation AND semantic checks
  invalid-schema/   - must FAIL JSON Schema validation (one fault each)
  invalid-semantic/ - pass schema but FAIL protocol semantic checks

Run validate.py afterwards to confirm every fixture behaves as expected.
"""
import json, os, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SCHEMA_SRC = os.path.join(ROOT, "..", "fetched", "schema-codex.json")
FIX = os.path.join(ROOT, "fixtures")

for sub in ("valid", "invalid-schema", "invalid-semantic"):
    os.makedirs(os.path.join(FIX, sub), exist_ok=True)

# copy canonical schema into the suite so it is self-contained
os.makedirs(os.path.join(ROOT, "schemas"), exist_ok=True)
shutil.copy(SCHEMA_SRC, os.path.join(ROOT, "schemas", "sovereign-event-v1.schema.json"))

TS = "2026-10-11T04:32:17Z"

def base(**over):
    ev = {
        "schema_version": "1.0",
        "event_id": "7f3a1c9e-2b4d-4e8a-9c5f-0a1b2c3d4e5f",
        "timestamp": TS,
        "source": "photonic-codex",
        "type": "service.health",
        "classification": "DEMONSTRATED",
        "correlation_id": None,
        "provenance": {
            "repository": "onegayunicorn/photonic-codex",
            "revision": "codex/foundation-runtime-audit@a1b2c3d",
            "evidence_uri": None,
        },
        "payload": {},
    }
    ev.update(over)
    return ev

def write(category, name, event):
    path = os.path.join(FIX, category, name)
    with open(path, "w") as f:
        json.dump(event, f, indent=2)
        f.write("\n")
    print(f"  {category}/{name}")

# ---- VALID fixtures (8) ---------------------------------------------------
print("Writing valid fixtures:")
write("valid", "01-codex-health-healthy.json", base(
    source="photonic-codex", type="service.health", classification="DEMONSTRATED",
    event_id="c0dex001-aaaa-4aaa-aaaa-000000000001",
    correlation_id="corr-daemon-boot-001",
    payload={"health": "HEALTHY", "module": "meta-hub", "uptime_s": 412, "observation_time": TS},
))
write("valid", "02-platform-capability-simulated.json", base(
    source="unicorn-sovereign-platform", type="capability.report", classification="SIMULATED",
    event_id="plat0001-bbbb-4bbb-bbbb-000000000002",
    provenance={"repository": "onegayunicorn/unicorn-sovereign-platform",
                "revision": "codex/integration-contract-v1@e5f6a7b",
                "evidence_uri": "tests/quantum_sim/test_photonic.py::test_single_photon_state"},
    payload={"module": "quantum-photonic-sim", "stage": 0, "status": "simulated",
             "qubits_simulated": 4, "note": "synthetic result, not physical hardware"},
))
write("valid", "03-platform-test-result-validated.json", base(
    source="unicorn-sovereign-platform", type="test.result", classification="VALIDATED",
    event_id="plat0002-cccc-4ccc-cccc-000000000003",
    correlation_id="corr-contract-v1",
    provenance={"repository": "onegayunicorn/unicorn-sovereign-platform",
                "revision": "codex/integration-contract-v1@e5f6a7b",
                "evidence_uri": "tests/contract/test_event_schema.py"},
    payload={"test_suite": "contract-v1", "passed": True, "criterion": "schema-validates",
             "assertions": 12, "duration_ms": 84},
))
write("valid", "04-codex-audit-measured.json", base(
    source="photonic-codex", type="audit.record", classification="MEASURED",
    event_id="c0dex002-dddd-4ddd-dddd-000000000004",
    payload={"log_ref": "ResonanceLogs/2026-10-11/0042", "entries": 17,
             "procedure": "daemon-event-ingest", "units": "events"},
))
write("valid", "05-nexus-receipt-unverified.json", base(
    source="quantum-multiversal-nexus", type="event.receipt", classification="UNVERIFIED",
    event_id="nexus001-eeee-4eee-eeee-000000000005",
    correlation_id="plat0001-bbbb-4bbb-bbbb-000000000002",
    provenance={"repository": "onegayunicorn/quantum-multiversal-nexus",
                "revision": None, "evidence_uri": None},
    payload={"mirrored_from": "unicorn-sovereign-platform", "original_event_id": "plat0001-bbbb-4bbb-bbbb-000000000002"},
))
write("valid", "06-nexus-health-unknown-stale.json", base(
    source="quantum-multiversal-nexus", type="service.health", classification="UNVERIFIED",
    event_id="nexus002-ffff-4fff-ffff-000000000006",
    provenance={"repository": "onegayunicorn/quantum-multiversal-nexus",
                "revision": "codex/integration-contract-v1@9c8d7e6", "evidence_uri": None},
    payload={"health": "UNKNOWN", "reason": "no platform report within staleness window",
             "last_seen": "2026-10-11T03:10:00Z", "observation_time": TS},
))
write("valid", "07-nexus-capability-proposed.json", base(
    source="quantum-multiversal-nexus", type="capability.report", classification="PROPOSED",
    event_id="nexus003-1111-4111-1111-000000000007",
    provenance={"repository": "onegayunicorn/quantum-multiversal-nexus",
                "revision": "codex/integration-contract-v1@9c8d7e6",
                "evidence_uri": "docs/manifest/6-domains.md"},
    payload={"domain": "ecosystem-coordination", "status": "proposed",
             "note": "nexus describes; platform must verify before execution"},
))
write("valid", "08-platform-health-degraded.json", base(
    source="unicorn-sovereign-platform", type="service.health", classification="DEMONSTRATED",
    event_id="plat0003-2222-4222-2222-000000000008",
    provenance={"repository": "onegayunicorn/unicorn-sovereign-platform",
                "revision": "codex/integration-contract-v1@e5f6a7b", "evidence_uri": None},
    payload={"health": "DEGRADED", "degraded_modules": ["npc-sandbox"],
             "healthy_modules": 8, "observation_time": TS},
))

# ---- INVALID-SCHEMA fixtures (12, one fault each) -------------------------
print("Writing invalid-schema fixtures:")
e = base(); del e["event_id"]; write("invalid-schema", "01-missing-required-event-id.json", e)
write("invalid-schema", "02-wrong-schema-version.json", base(schema_version="2.0"))
write("invalid-schema", "03-timestamp-no-trailing-z.json", base(timestamp="2026-10-11T04:32:17+00:00"))
write("invalid-schema", "04-timestamp-malformed.json", base(timestamp="yesterday"))
write("invalid-schema", "05-unknown-source.json", base(source="rogue-system"))
write("invalid-schema", "06-unknown-type-command.json", base(type="system.command"))
write("invalid-schema", "07-unknown-classification.json", base(classification="OPERATIONAL"))
e = base(); e["unexpected_field"] = True; write("invalid-schema", "08-extra-top-level-property.json", e)
write("invalid-schema", "09-payload-not-object.json", base(payload="not-an-object"))
write("invalid-schema", "10-event-id-too-long.json", base(event_id="x" * 129))
e = base(); e["provenance"]["extra"] = 1; write("invalid-schema", "11-provenance-extra-property.json", e)
write("invalid-schema", "12-correlation-id-wrong-type.json", base(correlation_id=12345))

# ---- INVALID-SEMANTIC fixtures (6: schema-valid, protocol-invalid) --------
print("Writing invalid-semantic fixtures:")
e = base(source="unicorn-sovereign-platform", type="capability.report", classification="SIMULATED",
         event_id="sem001-3333-4333-3333-000000000001",
         payload={"module": "quantum-photonic-sim", "status": "simulated"})
del e["provenance"]; write("invalid-semantic", "01-capability-without-provenance.json", e)
e = base(source="unicorn-sovereign-platform", type="test.result", classification="VALIDATED",
         event_id="sem002-4444-4444-4444-000000000002",
         payload={"test_suite": "x", "passed": True})
del e["provenance"]; write("invalid-semantic", "02-test-result-without-provenance.json", e)
write("invalid-semantic", "03-capability-empty-repository.json", base(
    source="quantum-multiversal-nexus", type="capability.report", classification="PROPOSED",
    event_id="sem003-5555-4555-5555-000000000003",
    provenance={"repository": "", "revision": None, "evidence_uri": None},
    payload={"domain": "x", "status": "proposed"}))
write("invalid-semantic", "04-health-value-not-allowed.json", base(
    source="photonic-codex", type="service.health", classification="DEMONSTRATED",
    event_id="sem004-6666-4666-6666-000000000004",
    payload={"health": "RUNNING_FINE"}))
write("invalid-semantic", "05-payload-contains-command.json", base(
    source="photonic-codex", type="audit.record", classification="MEASURED",
    event_id="sem005-7777-4777-7777-000000000005",
    payload={"command": "rm -rf /", "note": "v1 must not carry commands"}))
write("invalid-semantic", "06-payload-contains-credential.json", base(
    source="unicorn-sovereign-platform", type="capability.report", classification="SIMULATED",
    event_id="sem006-8888-4888-8888-000000000006",
    provenance={"repository": "onegayunicorn/unicorn-sovereign-platform", "revision": None, "evidence_uri": None},
    payload={"module": "x", "api_secret": "leaked-credential-must-be-rejected"}))

print("\nDone. Fixture tree:")
for cat in ("valid", "invalid-schema", "invalid-semantic"):
    n = len(os.listdir(os.path.join(FIX, cat)))
    print(f"  {cat}: {n} files")
