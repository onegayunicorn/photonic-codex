# Healing — Recovery Plans

**Maturity: PLANNED.** This domain stores recovery procedures and rollback plans; it does not execute privileged rollback automatically.

Every plan must specify trigger, preconditions, impact, backup requirements, dry-run output, operator approval, bounded execution, verification steps, and a stop/abort procedure. External writes remain disabled until an independently reviewed implementation is approved.
