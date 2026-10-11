"""Photonic Codex local API.
Read-only development baseline. This module deliberately exposes no shell,
filesystem mutation, arbitrary script execution, or external-write endpoint.

Persistent provenance (opt-in): set CODEX_PERSISTENT=1 to append events to
ResonanceLogs/store/events.jsonl with a tamper-evident SHA-256 hash chain.
Default remains process-memory for backwards compatibility.
"""
from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from flask import Flask, jsonify, request, send_from_directory
from provenance_store import open_store, utc_now, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parent
SERVICE_NAME = "photonic-codex"
API_VERSION = "v1"
EVENT_LIMIT = max(10, min(int(os.environ.get("CODEX_EVENT_LIMIT", "200")), 1000))
EXPORT_MAX = 10000
MODULES = [
    {"id": "brain", "path": "Brain/", "status": "PLANNED", "mode": "read-only"},
    {"id": "portals", "path": "Portals/", "status": "PLANNED", "mode": "read-only"},
    {"id": "shrine-nodes", "path": "ShrineNodes/", "status": "PLANNED", "mode": "read-only"},
    {"id": "resonance-logs", "path": "ResonanceLogs/", "status": "PROTOTYPE", "mode": "append-only"},
    {"id": "quantum-doors", "path": "quantum-doors/", "status": "PLANNED", "mode": "read-only"},
    {"id": "meta-hub", "path": "meta-hub.html", "status": "SKELETON", "mode": "read-only"},
    {"id": "lineage", "path": "lineage/", "status": "PROTOTYPE", "mode": "read-only"},
    {"id": "sandbox", "path": "sandbox/", "status": "PLANNED", "mode": "simulation-only"},
    {"id": "network", "path": "network/", "status": "PLANNED", "mode": "disabled-by-default"},
    {"id": "healing", "path": "healing/", "status": "PLANNED", "mode": "manual-approval"},
]
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

# Opt-in persistent store; default = in-memory (backwards compatible).
store = open_store(ROOT, maxlen=EVENT_LIMIT)


def record_event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Append a diagnostic event. Aligned to sovereign-event-v1 shared schema.

    source=photonic-codex, classification=MEASURED (local observation).
    Persists to disk when CODEX_PERSISTENT=1; otherwise process memory.
    """
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "source": "photonic-codex",
        "type": event_type,
        "classification": "MEASURED",
        "correlation_id": request.headers.get("X-Correlation-ID") if request else None,
        "provenance": {
            "repository": "onegayunicorn/photonic-codex",
            "revision": os.environ.get("CODEX_REVISION"),
            "evidence_uri": None,
        },
        "payload": payload or {},
    }
    return store.append(event)


@app.get("/")
def home():
    return send_from_directory(ROOT, "meta-hub.html")


@app.get("/api/v1/health")
def health():
    return jsonify({
        "status": "ok",
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "timestamp": utc_now(),
        "mode": "read-only-development",
        "event_retention": store.retention,
        "durable": store.durable,
    })


@app.get("/api/v1/modules")
def modules():
    return jsonify({"api_version": API_VERSION, "modules": MODULES})


@app.get("/api/v1/events")
def events():
    try:
        limit = int(request.args.get("limit", "50"))
    except ValueError:
        return jsonify({"error": {"code": "invalid_limit", "message": "limit must be an integer"}}), 400
    if not 1 <= limit <= 200:
        return jsonify({"error": {"code": "limit_out_of_range", "message": "limit must be between 1 and 200"}}), 400
    snapshot = store.list(limit=limit)
    body = {
        "events": snapshot,
        "retention": store.retention,
        "durable": store.durable,
        "count": store.count(),
    }
    if store.durable:
        body["integrity"] = store.verify()
    return jsonify(body)


@app.get("/api/v1/provenance/integrity")
def provenance_integrity():
    """Read-only hash-chain verification. Never treats errors as healthy."""
    result = store.verify()
    status_code = 200 if result.get("status") in ("OK", "EMPTY", "NOT_APPLICABLE") else 500
    return jsonify({"service": SERVICE_NAME, "durable": store.durable, "integrity": result}), status_code


@app.get("/api/v1/provenance/export")
def provenance_export():
    """Read-only full log export (seq + entry_hash per event). Audit use."""
    events_out = store.export()[-EXPORT_MAX:]
    return jsonify({
        "service": SERVICE_NAME,
        "count": len(events_out),
        "retention": store.retention,
        "integrity": store.verify(),
        "events": events_out,
    })


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": {"code": "not_found", "message": "route not found"}}), 404


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": {"code": "payload_too_large", "message": "request body exceeds limit"}}), 413


if __name__ == "__main__":
    host = os.environ.get("CODEX_HOST", "127.0.0.1")
    port = int(os.environ.get("CODEX_PORT", "7070"))
    # Debug/reloader deliberately disabled; remote binding is an operator choice.
    app.run(host=host, port=port, debug=False, use_reloader=False)
