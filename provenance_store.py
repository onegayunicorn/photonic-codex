"""Photonic Codex — persistent provenance store.

Storage abstraction behind /api/v1/events. Two backends:

  MemoryStore     — original process-memory deque (default, backwards compatible).
  PersistentStore — append-only JSONL log with a tamper-evident SHA-256 hash
                    chain, integrity verification, export, and logical rollback.

Honesty boundary (per docs/protocol.md): hash chaining makes the log
TAMPER-EVIDENT, not immutable or tamper-proof. Physical deletion protection
requires filesystem/OS access controls this module does not provide.

Zero third-party dependencies: stdlib json/hashlib/threading only.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# --- shared contract v1 constants (mirrors schemas/sovereign-event-v1.schema.json) ---
SCHEMA_VERSION = "1.0"
ALLOWED_SOURCES = {"photonic-codex", "unicorn-sovereign-platform", "quantum-multiversal-nexus"}
ALLOWED_TYPES = {"service.health", "capability.report", "test.result", "audit.record", "event.receipt"}
ALLOWED_CLASSIFICATIONS = {"PROPOSED", "SIMULATED", "DEMONSTRATED", "MEASURED", "UNVERIFIED", "VALIDATED"}
REQUIRED_FIELDS = {"schema_version", "event_id", "timestamp", "source", "type", "classification", "payload"}
GENESIS_PREV_HASH = "0" * 64
SUPERSEDE_ACTION = "logical_rollback"  # payload.action for rollback audit markers


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(obj: Any) -> bytes:
    """Stable serialization for hashing: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def entry_hash(seq: int, prev_hash: str, event: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json({"seq": seq, "prev_hash": prev_hash, "event": event})).hexdigest()


def validate_event(event: dict[str, Any]) -> list[str]:
    """Lightweight sovereign-event-v1 validation. Returns list of errors (empty = valid).

    Mirrors the JSON Schema + the semantic rules from docs/protocol.md so the
    store never persists a contract-invalid event. (No jsonschema dependency.)
    """
    errs: list[str] = []
    if not isinstance(event, dict):
        return ["event must be a JSON object"]
    missing = REQUIRED_FIELDS - set(event)
    if missing:
        errs.append(f"missing required fields: {sorted(missing)}")
    if event.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if event.get("source") not in ALLOWED_SOURCES:
        errs.append(f"source {event.get('source')!r} not in {sorted(ALLOWED_SOURCES)}")
    if event.get("type") not in ALLOWED_TYPES:
        errs.append(f"type {event.get('type')!r} not in {sorted(ALLOWED_TYPES)}")
    if event.get("classification") not in ALLOWED_CLASSIFICATIONS:
        errs.append(f"classification {event.get('classification')!r} not in {sorted(ALLOWED_CLASSIFICATIONS)}")
    ts = event.get("timestamp")
    if not isinstance(ts, str) or not ts.endswith("Z"):
        errs.append("timestamp must be UTC ISO-8601 with trailing Z")
    if not isinstance(event.get("payload"), dict):
        errs.append("payload must be an object")
    cid = event.get("correlation_id", None)
    if cid is not None and not isinstance(cid, str):
        errs.append("correlation_id must be string or null")
    # semantic: capability.report / test.result require provenance with non-empty repository
    if event.get("type") in {"capability.report", "test.result"}:
        prov = event.get("provenance")
        if not isinstance(prov, dict) or not isinstance(prov.get("repository"), str) or not prov.get("repository").strip():
            errs.append(f"{event.get('type')} requires provenance.repository (non-empty)")
    return errs


class MemoryStore:
    """Original in-memory behaviour. Default until operator enables persistence."""

    durable = False
    retention = "process-memory"

    def __init__(self, maxlen: int = 200):
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._events.append(event)
        return event

    def list(self, limit: int = 50, include_superseded: bool = True) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)[-limit:]

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def verify(self) -> dict[str, Any]:
        return {"status": "NOT_APPLICABLE", "reason": "in-memory store has no chain to verify"}

    def export(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)


class PersistentStore:
    """Append-only JSONL log with SHA-256 hash chain.

    File layout (one JSON object per line):
      {"seq": N, "prev_hash": <64 hex>, "entry_hash": <64 hex>, "event": {...sovereign envelope...}}

    Logical rollback appends an audit.record marker with
      payload.action = "logical_rollback", payload.supersedes_after = <seq>
    Events after that seq are excluded from default queries but remain in the
    log (chain integrity preserved). Physical truncation is intentionally not
    implemented; see healing/ module for operator-controlled restore.
    """

    durable = True
    retention = "append-only-jsonl"

    def __init__(self, data_dir: Path, seal_path: Path | None = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.data_dir / "events.jsonl"
        self.seal_path = Path(seal_path) if seal_path else self.data_dir / "seal.json"
        self._lock = threading.Lock()
        self._index: list[dict[str, Any]] = []  # cached parsed lines
        self._load_index()

    # -- internal ---------------------------------------------------------
    def _load_index(self) -> None:
        self._index = []
        if not self.log_path.exists():
            return
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._index.append(json.loads(line))

    def _last(self) -> dict[str, Any] | None:
        return self._index[-1] if self._index else None

    def _supersedes_after(self) -> int | None:
        """Largest seq marked superseded by the latest logical-rollback marker."""
        bound: int | None = None
        for rec in self._index:
            ev = rec.get("event", {})
            if ev.get("type") == "audit.record" and ev.get("payload", {}).get("action") == SUPERSEDE_ACTION:
                after = ev.get("payload", {}).get("supersedes_after")
                if isinstance(after, int):
                    bound = after if bound is None else max(bound, after)
        return bound

    # -- public API -------------------------------------------------------
    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        errs = validate_event(event)
        if errs:
            raise ValueError(f"refusing to persist contract-invalid event: {errs}")
        with self._lock:
            last = self._last()
            seq = (last["seq"] + 1) if last else 1
            prev = last["entry_hash"] if last else GENESIS_PREV_HASH
            eh = entry_hash(seq, prev, event)
            rec = {"seq": seq, "prev_hash": prev, "entry_hash": eh, "event": event}
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self._index.append(rec)
            return rec

    def list(self, limit: int = 50, include_superseded: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            bound = None if include_superseded else self._supersedes_after()
            out = [r["event"] for r in self._index if bound is None or r["seq"] <= bound]
            return out[-limit:]

    def count(self, include_superseded: bool = False) -> int:
        with self._lock:
            if include_superseded:
                return len(self._index)
            bound = self._supersedes_after()
            return sum(1 for r in self._index if bound is None or r["seq"] <= bound)

    def verify(self) -> dict[str, Any]:
        """Recompute the hash chain. Returns status OK / TAMPERED / GAP / EMPTY."""
        with self._lock:
            if not self._index:
                return {"status": "EMPTY", "count": 0}
            prev = GENESIS_PREV_HASH
            expected_seq = 1
            for rec in self._index:
                if rec["seq"] != expected_seq:
                    return {"status": "GAP", "at_seq": rec["seq"], "expected_seq": expected_seq,
                            "count": len(self._index)}
                if rec["prev_hash"] != prev:
                    return {"status": "TAMPERED", "at_seq": rec["seq"],
                            "reason": "prev_hash mismatch (chain broken before this entry)",
                            "count": len(self._index)}
                recomputed = entry_hash(rec["seq"], rec["prev_hash"], rec["event"])
                if recomputed != rec["entry_hash"]:
                    return {"status": "TAMPERED", "at_seq": rec["seq"],
                            "reason": "entry_hash mismatch (event or metadata modified)",
                            "count": len(self._index)}
                prev = rec["entry_hash"]
                expected_seq += 1
            seal_note = {}
            if self.seal_path.exists():
                try:
                    seal = json.loads(self.seal_path.read_text(encoding="utf-8"))
                    seal_note = {"seal_matches": seal.get("last_hash") == prev,
                                 "seal_last_seq": seal.get("last_seq")}
                except Exception:
                    seal_note = {"seal_matches": False, "seal_error": "seal file unreadable"}
            return {"status": "OK", "count": len(self._index), "last_seq": self._index[-1]["seq"],
                    "last_hash": prev, **seal_note}

    def export(self, include_superseded: bool = True) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r["event"], seq=r["seq"], entry_hash=r["entry_hash"]) for r in self._index]

    def checkpoint(self) -> dict[str, Any]:
        """Write a seal file with the current chain tip. Operator/CLI use only."""
        with self._lock:
            last = self._last()
            seal = {"seal_version": 1, "sealed_at": utc_now(),
                    "count": len(self._index),
                    "last_seq": last["seq"] if last else 0,
                    "last_hash": last["entry_hash"] if last else GENESIS_PREV_HASH,
                    "note": "tamper-evident checkpoint, not proof of immutability"}
            self.seal_path.parent.mkdir(parents=True, exist_ok=True)
            self.seal_path.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
            return seal

    def logical_rollback(self, supersedes_after: int, reason: str, operator: str = "local-operator") -> dict[str, Any]:
        """Append a rollback marker; events after `supersedes_after` are hidden from default queries.

        Returns the marker record. Raises ValueError if supersedes_after is beyond current tip.
        Physical log is NEVER modified by this method.
        """
        with self._lock:
            tip = self._index[-1]["seq"] if self._index else 0
        if supersedes_after > tip:
            raise ValueError(f"supersedes_after={supersedes_after} beyond current tip={tip}")
        marker = {
            "schema_version": SCHEMA_VERSION,
            "event_id": _uuid(),
            "timestamp": utc_now(),
            "source": "photonic-codex",
            "type": "audit.record",
            "classification": "MEASURED",
            "correlation_id": None,
            "provenance": {"repository": "onegayunicorn/photonic-codex", "revision": None, "evidence_uri": None},
            "payload": {"action": SUPERSEDE_ACTION, "supersedes_after": supersedes_after,
                        "reason": reason[:500], "operator": operator[:128],
                        "note": "logical rollback; physical log retained, chain intact"},
        }
        return self.append(marker)


def _uuid() -> str:
    import uuid
    return str(uuid.uuid4())


def open_store(root: Path, maxlen: int = 200) -> MemoryStore | PersistentStore:
    """Factory. Persistence is opt-in via CODEX_PERSISTENT=1 (or any truthy value).

    Default = MemoryStore so existing behaviour and tests are unchanged.
    """
    if os.environ.get("CODEX_PERSISTENT", "").lower() in {"1", "true", "yes", "on"}:
        data_dir = Path(os.environ.get("CODEX_DATA_DIR", str(root / "ResonanceLogs" / "store")))
        seal_path = root / "lineage" / "seal.json"
        return PersistentStore(data_dir, seal_path=seal_path)
    return MemoryStore(maxlen=maxlen)
