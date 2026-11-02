# Security Policy

## Current status

Photonic Codex is early-stage software. Do not expose the development server directly to the public internet, use it as an authentication boundary, or connect it to privileged hardware or production systems.

## Safe defaults

- Loopback bind by default.
- No arbitrary command execution over HTTP.
- External adapters and external writes disabled until explicitly implemented and reviewed.
- Never commit tokens, passwords, private keys, device identifiers that should remain private, or production data.
- Treat logs and event records as potentially sensitive.
- Run with the least privileges possible.

## Reporting

Please report suspected vulnerabilities privately to the repository owner through GitHub's private vulnerability reporting feature where available. Include the affected commit, reproduction steps, impact, and suggested mitigation. Avoid posting secrets or exploitable details in a public issue.

## Release gate

A release must not be marked production-ready until dependency review, input validation tests, network exposure review, secret scanning, negative-path tests, and documented recovery procedures pass.
