# Portals — Entry-Point Adapters

**Maturity: PLANNED.** UI/API adapters belong here; the current dashboard entry point is the repository-root `meta-hub.html` served by `server.py`.

## Responsibilities
- Document each public entry point and its API contract.
- Keep browser presentation separate from privileged operations.
- Validate input at the API boundary.

## Boundaries
- No secrets in client code.
- No direct shell or filesystem mutation from a portal.
- Remote access remains disabled until authentication and authorization are implemented.
