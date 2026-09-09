# 12 — Testing, SECA, and Quality

Required tests: schema validation, lifecycle transitions, invalid transition rejection, dependency blocking, dependency cycle rejection, unknown dependency rejection, permissions binding, event emission, idempotency, retry behavior, proof gating, closure reconciliation, lane fairness, lane concurrency ceilings, queue backpressure, storm-size limits, GAQC evidence handling, GAQC escalation, and bounded high-volume storm behavior.

## GAQC

GAQC (Ghost Atlas Quality Control) is the packet-storm quality interception layer before SECA. Default policy deterministically samples LOW and MEDIUM risk work and inspects HIGH/CRITICAL work at 100%.

GAQC may:
- pass or bypass a packet onward to SECA;
- route evidence/quality rework to DEVOS;
- quarantine high-severity defects for SECA;
- escalate critical defects to JANUS.

GAQC may not call itself the verification authority and may not produce PROVED/CLOSED truth.

## SECA

SECA independently verifies high-value workflow invariants. A packet cannot reach PROVED or CLOSED when its required proof class is absent or rejected. The executable kernel enforces the same boundary as `REVIEW -> VERIFIED -> COMPLETED`.

## Packet-storm acceptance

A storm is healthy when it preserves every packet under saturation, releases dependencies only after upstream closure, respects lane concurrency, services weighted lanes without starvation, records backpressure, and maintains evidence/provenance through every handoff.

Minimum load proof for v0.2: a synthetic 100-packet storm must admit eligible work while limiting simultaneous claims to declared lane capacity.
