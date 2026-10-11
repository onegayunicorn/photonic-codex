#!/usr/bin/env python3
"""Sovereign Ecosystem Event v1 — contract validation suite.

Validates fixtures against schemas/sovereign-event-v1.schema.json AND the
semantic rules from docs/protocol.md that JSON Schema alone cannot enforce.

Usage:
    python3 validate.py            # run all fixture checks, exit non-zero on failure
    python3 validate.py <file>...  # validate specific event files (report only)

Exit code 0 = every fixture met its category expectation.
"""
import json, os, re, sys

try:
    import jsonschema
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError
except ImportError:
    sys.exit("ERROR: install deps:  pip install jsonschema rfc3339-validator")

ROOT = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(ROOT, "schemas", "sovereign-event-v1.schema.json")
FIXTURES = os.path.join(ROOT, "fixtures")

ALLOWED_HEALTH = {"HEALTHY", "DEGRADED", "UNAVAILABLE", "UNKNOWN"}
TYPES_REQUIRING_PROVENANCE = {"capability.report", "test.result"}
CRED_KEY_RE = re.compile(r"(password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|bearer)", re.I)
COMMAND_KEYS = {"command", "execute", "script", "shell", "cmd", "run", "deploy", "rollback", "git_push"}

with open(SCHEMA_PATH) as f:
    SCHEMA = json.load(f)

# format checker enforces "format": "date-time" (needs rfc3339-validator installed)
try:
    format_checker = Draft202012Validator.FORMAT_CHECKER
except Exception:
    format_checker = None
validator = Draft202012Validator(SCHEMA, format_checker=format_checker)


def schema_errors(event):
    """Return list of schema validation error messages (empty = valid)."""
    return [e.message for e in validator.iter_errors(event)]


def semantic_errors(event):
    """Protocol-level rules from docs/protocol.md. Returns list of messages."""
    errs = []
    typ = event.get("type")
    payload = event.get("payload") or {}
    prov = event.get("provenance")

    # Rule: capability.report and test.result MUST include provenance with non-empty repository
    if typ in TYPES_REQUIRING_PROVENANCE:
        if not isinstance(prov, dict):
            errs.append(f"{typ} requires provenance object (protocol §Event envelope)")
        elif not isinstance(prov.get("repository"), str) or not prov.get("repository").strip():
            errs.append(f"{typ} provenance.repository must be a non-empty string")

    # Rule: service.health payload.health must use canonical health values
    if typ == "service.health" and isinstance(payload, dict) and "health" in payload:
        if payload["health"] not in ALLOWED_HEALTH:
            errs.append(f"health value {payload['health']!r} not in {sorted(ALLOWED_HEALTH)}")

    # Rule: payload must never include credentials
    if isinstance(payload, dict):
        for k in payload:
            if CRED_KEY_RE.search(k):
                errs.append(f"payload key {k!r} matches credential pattern (forbidden)")

    # Rule: v1 does not authorize command execution / deployment / git push
    if isinstance(payload, dict):
        for k in payload:
            if k.lower() in COMMAND_KEYS:
                errs.append(f"payload key {k!r} is a command/write action not authorized by v1")

    return errs


def validate_file(path):
    with open(path) as f:
        event = json.load(f)
    se = schema_errors(event)
    me = semantic_errors(event)
    return se, me


def run_fixture_suite():
    results = {"pass": 0, "fail": 0}
    failures = []

    def check(category, path, expect_schema_pass, expect_semantic_pass):
        nonlocal failures
        try:
            se, me = validate_file(path)
        except Exception as exc:
            results["fail"] += 1
            failures.append(f"{category}/{os.path.basename(path)}: parse error: {exc}")
            print(f"  FAIL  {category}/{os.path.basename(path)}  (parse error)")
            return
        got_schema_pass = not se
        got_semantic_pass = not me
        ok = (got_schema_pass == expect_schema_pass) and (
            expect_semantic_pass is None or got_semantic_pass == expect_semantic_pass
        )
        tag = "ok  " if ok else "FAIL"
        results["pass" if ok else "fail"] += 1
        detail = ""
        if not ok:
            exp = f"expected schema_pass={expect_schema_pass}, semantic_pass={expect_semantic_pass}; got {got_schema_pass}/{got_semantic_pass}"
            if se: detail += f" | schema: {'; '.join(se[:2])}"
            if me: detail += f" | semantic: {'; '.join(me[:2])}"
            failures.append(f"{category}/{os.path.basename(path)}: {exp}{detail}")
        print(f"  {tag}  {category}/{os.path.basename(path)}{detail}")

    print("== valid/ (must pass schema + semantic) ==")
    for name in sorted(os.listdir(os.path.join(FIXTURES, "valid"))):
        check("valid", os.path.join(FIXTURES, "valid", name), True, True)

    print("\n== invalid-schema/ (must FAIL schema) ==")
    for name in sorted(os.listdir(os.path.join(FIXTURES, "invalid-schema"))):
        check("invalid-schema", os.path.join(FIXTURES, "invalid-schema", name), False, None)

    print("\n== invalid-semantic/ (schema passes, semantic must FAIL) ==")
    for name in sorted(os.listdir(os.path.join(FIXTURES, "invalid-semantic"))):
        check("invalid-semantic", os.path.join(FIXTURES, "invalid-semantic", name), True, False)

    print(f"\n{results['pass']} passed, {results['fail']} failed")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("ALL FIXTURES BEHAVE AS EXPECTED — contract v1 consistent.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        bad = 0
        for p in sys.argv[1:]:
            se, me = validate_file(p)
            status = "VALID" if not se and not me else "INVALID"
            if se or me: bad += 1
            print(f"{status}  {p}")
            for m in se: print(f"    schema: {m}")
            for m in me: print(f"    semantic: {m}")
        sys.exit(1 if bad else 0)
    sys.exit(run_fixture_suite())
