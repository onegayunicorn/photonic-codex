# Brain — Coordination Contracts

**Maturity: PLANNED.** This directory owns coordination metadata and decision contracts, not an autonomous unrestricted execution engine.

## Responsibilities
- Define typed requests and decision records.
- Require source, evidence classification, and correlation ID for cross-module decisions.
- Separate proposed recommendations from approved actions.

## Boundaries
- No shell execution, credential storage, or implicit privilege escalation.
- No decision may upgrade another component's evidence label.
- Future implementation requires schema validation and deterministic unit tests.
