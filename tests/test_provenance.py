"""Tests for persistent provenance store. Hermetic: uses temp directories."""
import importlib
import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path

import provenance_store
from provenance_store import (
    PersistentStore, MemoryStore, open_store, validate_event, utc_now, SCHEMA_VERSION,
)


def make_event(**over):
    ev = {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "source": "photonic-codex",
        "type": "audit.record",
        "classification": "MEASURED",
        "correlation_id": None,
        "provenance": {"repository": "onegayunicorn/photonic-codex", "revision": None, "evidence_uri": None},
        "payload": {"k": "v"},
    }
    ev.update(over)
    return ev


class ValidatorTests(unittest.TestCase):
    def test_valid_event_passes(self):
        self.assertEqual(validate_event(make_event()), [])

    def test_invalid_source_rejected(self):
        errs = validate_event(make_event(source="codex-api"))  # legacy value, not in contract
        self.assertTrue(any("source" in e for e in errs))

    def test_invalid_classification_rejected(self):
        errs = validate_event(make_event(classification="DERIVED"))
        self.assertTrue(any("classification" in e for e in errs))

    def test_capability_requires_provenance(self):
        ev = make_event(type="capability.report")
        del ev["provenance"]
        errs = validate_event(ev)
        self.assertTrue(any("provenance" in e for e in errs))

    def test_timestamp_must_end_with_z(self):
        errs = validate_event(make_event(timestamp="2026-10-11T00:00:00+00:00"))
        self.assertTrue(any("trailing Z" in e for e in errs))


class MemoryStoreTests(unittest.TestCase):
    def test_default_is_memory_and_non_durable(self):
        store = open_store(Path(tempfile.mkdtemp()))
        self.assertIsInstance(store, MemoryStore)
        self.assertFalse(store.durable)
        self.assertEqual(store.retention, "process-memory")

    def test_memory_append_and_list(self):
        store = MemoryStore(maxlen=5)
        for i in range(3):
            store.append(make_event(payload={"i": i}))
        self.assertEqual(store.count(), 3)
        self.assertEqual(len(store.list(limit=10)), 3)


class PersistentStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.store = PersistentStore(self.dir, seal_path=self.dir / "seal.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_persists_across_reload(self):
        for i in range(3):
            self.store.append(make_event(payload={"i": i}))
        reloaded = PersistentStore(self.dir, seal_path=self.dir / "seal.json")
        self.assertEqual(reloaded.count(), 3)
        self.assertEqual(reloaded.verify()["status"], "OK")

    def test_hash_chain_verify_ok(self):
        for i in range(5):
            self.store.append(make_event())
        v = self.store.verify()
        self.assertEqual(v["status"], "OK")
        self.assertEqual(v["last_seq"], 5)
        self.assertEqual(len(v["last_hash"]), 64)

    def test_tamper_detection(self):
        for i in range(3):
            self.store.append(make_event())
        # corrupt the middle line's event payload
        lines = self.dir.joinpath("events.jsonl").read_text().splitlines()
        rec = json.loads(lines[1])
        rec["event"]["payload"]["k"] = "TAMPERED"
        lines[1] = json.dumps(rec)
        self.dir.joinpath("events.jsonl").write_text("\n".join(lines) + "\n")
        reloaded = PersistentStore(self.dir, seal_path=self.dir / "seal.json")
        v = reloaded.verify()
        self.assertEqual(v["status"], "TAMPERED")
        self.assertEqual(v["at_seq"], 2)

    def test_gap_detection(self):
        for i in range(3):
            self.store.append(make_event())
        lines = self.dir.joinpath("events.jsonl").read_text().splitlines()
        del lines[1]  # delete middle entry -> seq jumps 1 -> 3
        self.dir.joinpath("events.jsonl").write_text("\n".join(lines) + "\n")
        reloaded = PersistentStore(self.dir, seal_path=self.dir / "seal.json")
        self.assertEqual(reloaded.verify()["status"], "GAP")

    def test_invalid_event_refused_at_append(self):
        with self.assertRaises(ValueError):
            self.store.append(make_event(source="rogue"))

    def test_export_includes_chain_metadata(self):
        for i in range(3):
            self.store.append(make_event())
        exp = self.store.export()
        self.assertEqual(len(exp), 3)
        self.assertEqual(exp[0]["seq"], 1)
        self.assertTrue(all("entry_hash" in e for e in exp))

    def test_logical_rollback_hides_later_entries_but_keeps_chain(self):
        for i in range(5):
            self.store.append(make_event(payload={"i": i}))
        marker = self.store.logical_rollback(supersedes_after=3, reason="test rollback")
        self.assertEqual(marker["seq"], 6)
        # default queries exclude superseded entries (seq > 3) + the marker itself (seq 6 > 3)
        self.assertEqual(self.store.count(), 3)
        self.assertEqual(len(self.store.list(limit=50)), 3)
        # full log retained, chain still verifies
        self.assertEqual(self.store.count(include_superseded=True), 6)
        self.assertEqual(self.store.verify()["status"], "OK")

    def test_rollback_beyond_tip_raises(self):
        self.store.append(make_event())
        with self.assertRaises(ValueError):
            self.store.logical_rollback(supersedes_after=99, reason="nope")

    def test_checkpoint_seal_matches(self):
        for i in range(2):
            self.store.append(make_event())
        seal = self.store.checkpoint()
        self.assertTrue(self.dir.joinpath("seal.json").exists())
        v = self.store.verify()
        self.assertTrue(v.get("seal_matches"))
        self.assertEqual(v.get("seal_last_seq"), 2)


class PersistentHttpTests(unittest.TestCase):
    """Reload server with CODEX_PERSISTENT=1 pointing at a temp dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["CODEX_PERSISTENT"] = "1"
        os.environ["CODEX_DATA_DIR"] = str(Path(self.tmp.name) / "store")
        import server
        self.server = importlib.reload(server)
        self.client = self.server.app.test_client()

    def tearDown(self):
        del os.environ["CODEX_PERSISTENT"]
        del os.environ["CODEX_DATA_DIR"]
        import server
        importlib.reload(server)
        self.tmp.cleanup()

    def test_events_endpoint_reports_durable_and_integrity(self):
        # record an event via request context so it lands in the persistent store
        with self.server.app.test_request_context("/", headers={"X-Correlation-ID": "cid-1"}):
            self.server.record_event("audit.record", {"boot": True})
        r = self.client.get("/api/v1/events?limit=5")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["durable"])
        self.assertEqual(body["retention"], "append-only-jsonl")
        self.assertEqual(body["integrity"]["status"], "OK")
        self.assertGreaterEqual(body["count"], 1)

    def test_integrity_endpoint(self):
        r = self.client.get("/api/v1/provenance/integrity")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["durable"])

    def test_export_endpoint(self):
        r = self.client.get("/api/v1/provenance/export")
        self.assertEqual(r.status_code, 200)
        self.assertIn("events", r.get_json())


if __name__ == "__main__":
    unittest.main()
