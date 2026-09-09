# 12 — Testing, SECA, and Quality

Required tests: schema validation, lifecycle transitions, invalid transition rejection, dependency blocking, permissions binding, event emission, idempotency, retry behavior, proof gating, and closure reconciliation.

SECA independently verifies high-value workflow invariants. A packet cannot reach PROVED or CLOSED when its required proof class is absent or rejected.