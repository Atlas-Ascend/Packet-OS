# 13 — Observability, Health, and Failure

Metrics: packets by state/type/owner, queue age, blocked duration, routing latency, execution latency, verification latency, proof rejection rate, retries, orphan dependencies, closure rate, storm packet count, storm critical-path length, wave count, lane queued/in-flight/capacity, lane backpressure events, GAQC pass/rework/quarantine/escalation counts.

`PacketStorm.snapshot()` is the canonical in-process observability surface for storm and lane state. Runtime transports may publish the same shape to Runtime Observatory and JANUS VIBE.

Failures remain explicit states. No packet disappears because a worker crashes or a lane saturates. Backpressure preserves the original authorized packet. Dead-letter, quarantine, rework, and escalation flows preserve packet identity, dependency lineage, evidence, and storm identity.

Failure routing:
- implementation defect -> DEVOS
- GAQC evidence/quality deficiency -> DEVOS
- GAQC high-severity defect -> SECA quarantine
- GAQC critical defect -> JANUS
- finish/proof ambiguity -> SECA
- worker availability -> Workforce Spine
- capability availability -> CrownGrid

Runtime Observatory consumes packet events and storm/lane snapshots for system-level health.
