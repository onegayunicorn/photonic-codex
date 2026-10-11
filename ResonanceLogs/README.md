# ResonanceLogs — Event History

**Maturity: PLANNED.** This directory is reserved for structured event history and provenance references.

The current API event buffer is process-local memory and is not durable. Before writing persistent records here, define retention, access controls, redaction, schema versioning, backup, and recovery. Hashes alone do not guarantee immutability.
