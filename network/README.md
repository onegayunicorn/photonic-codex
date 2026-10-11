# Network — Transport Adapters

**Maturity: PLANNED; remote transport disabled by default.** Future HTTP/WebSocket adapters must implement an allow-listed message schema, authentication, authorization, size limits, timeouts, replay controls, and structured errors.

Never forward arbitrary shell commands, credentials, or unvalidated paths. Network errors and stale reports must result in UNKNOWN/UNAVAILABLE rather than HEALTHY.
