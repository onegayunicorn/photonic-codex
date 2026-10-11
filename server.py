"""Photonic Codex local API.

Read-only development baseline. This module deliberately exposes no shell,
filesystem mutation, arbitrary script execution, or external-write endpoint.
"""
from __future__ import annotations

import os
import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
SERVICE_NAME = "photonic-codex"
API_VERSION = "v1"
EVENT_LIMIT = max(10, min(int(os.environ.get("CODEX_EVENT_LIMIT", "200")), 1000))

MODULES = [
    {"id": "brain", "path": "Brain/", "status": "PLANNED", "mode": "read-only"},
    {"id": "portals", "path": "Portals/", "status": "PLANNED", "mode": "read-only"},
    {"id": "shrine-nodes", "path": "ShrineNodes/", "status": "PLANNED", "mode": "read-only"},
    {"id": "resonance-logs", "path": "ResonanceLogs/", "status": "PLANNED", "mode": "read-only"},
    {"id": "quantum-doors", "path": "quantum-doors/", "status": "PLANNED", "mode": "read-only"},
    {"id": "meta-hub", "path": "meta-hub.html", "status": "SKELETON", "mode": "read-only"},
    {"id": "lineage", "path": "lineage/", "status": "PLANNED", "mode": "read-only"},
    {"id": "sandbox", "path": "sandbox/", "status": "PLANNED", "mode": "simulation-only"},
    {"id": "network", "path": "network/", "status": "PLANNED", "mode": "disabled-by-default"},
    {"id": "healing", "path": "healing/", "status": "PLANNED", "mode": "manual-approval"},
]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
_events: deque[dict[str, Any]] = deque(maxlen=EVENT_LIMIT)
_events_lock = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def record_event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Append a bounded diagnostic event to process memory."""
    event = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "source": "codex-api",
        "type": event_type,
        "classification": "DERIVED",
        "correlation_id": request.headers.get("X-Correlation-ID") if request else None,
        "payload": payload or {},
    }
    with _events_lock:
        _events.append(event)
    return event


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
    with _events_lock:
        snapshot = list(_events)[-limit:]
    return jsonify({"events": snapshot, "retention": "process-memory", "durable": False})


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
