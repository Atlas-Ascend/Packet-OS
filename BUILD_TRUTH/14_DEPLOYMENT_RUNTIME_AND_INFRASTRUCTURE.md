# 14 — Deployment, Runtime, and Infrastructure

Packet OS is deployment-neutral. Canonical production target may run as a service/API plus durable state store and event publisher, with local adapters on EDEN/ARK where required.

Infrastructure must provide durable packet ids/state, transactional or idempotent transitions, authenticated interfaces, event delivery, health endpoint, and backup/recovery.

Runtime location never changes packet semantics.