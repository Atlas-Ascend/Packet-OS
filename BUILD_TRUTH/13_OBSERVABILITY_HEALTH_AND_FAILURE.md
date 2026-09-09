# 13 — Observability, Health, and Failure

Metrics: packets by state/type/owner, queue age, blocked duration, routing latency, execution latency, verification latency, proof rejection rate, retries, orphan dependencies, closure rate.

Failures remain explicit states. No packet disappears because a worker crashes. Dead-letter and escalation flows preserve the original packet and evidence.

Runtime Observatory consumes packet events for system-level health.