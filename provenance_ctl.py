#!/usr/bin/env python3
"""Photonic Codex provenance operator CLI.

Local operator tool — NOT exposed over HTTP. v1 read-only contract preserved:
all mutations here are local-file and operator-initiated. Logical rollback
never physically deletes log entries; it appends a supersede marker.

Usage:
  python provenance_ctl.py verify [--data-dir DIR]
  python provenance_ctl.py export [--data-dir DIR] [--out FILE]
  python provenance_ctl.py checkpoint [--data-dir DIR]
  python provenance_ctl.py rollback --seq N --reason "..." [--operator NAME] [--data-dir DIR]
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "ResonanceLogs" / "store"
DEFAULT_SEAL = ROOT / "lineage" / "seal.json"


def load_store(args):
    from provenance_store import PersistentStore
    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA
    return PersistentStore(data_dir, seal_path=DEFAULT_SEAL)


def cmd_verify(args):
    store = load_store(args)
    print(json.dumps(store.verify(), indent=2))


def cmd_export(args):
    store = load_store(args)
    events = store.export()
    payload = json.dumps({"count": len(events), "events": events}, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"exported {len(events)} entries -> {args.out}")
    else:
        print(payload)


def cmd_checkpoint(args):
    store = load_store(args)
    print(json.dumps(store.checkpoint(), indent=2))


def cmd_rollback(args):
    store = load_store(args)
    rec = store.logical_rollback(supersedes_after=args.seq, reason=args.reason,
                                 operator=args.operator or "local-operator")
    print(json.dumps({"rolled_back": True, "supersedes_after": args.seq,
                      "marker_event_id": rec["event"]["event_id"],
                      "marker_seq": rec["seq"],
                      "note": "physical log retained; later entries hidden from default queries"}, indent=2))


def main():
    p = argparse.ArgumentParser(description="Codex provenance operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("verify", cmd_verify), ("export", cmd_export),
                     ("checkpoint", cmd_checkpoint), ("rollback", cmd_rollback)):
        sp = sub.add_parser(name)
        sp.add_argument("--data-dir", default=None, help=f"default: {DEFAULT_DATA}")
        if name == "export":
            sp.add_argument("--out", default=None, help="write JSON to file instead of stdout")
        if name == "rollback":
            sp.add_argument("--seq", type=int, required=True, help="supersede entries after this seq")
            sp.add_argument("--reason", required=True, help="audit reason (max 500 chars)")
            sp.add_argument("--operator", default="local-operator")
        sp.set_defaults(func=fn)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
