# Estate Integration

## Command-to-proof loop

1. Atlas Mind proposes structured work from operator/case context.
2. MAAT CaseGraph contributes referenced context where applicable.
3. JANUS approves intent and supplies an authorization reference.
4. Packet OS normalizes that intent into `packet/v1` and moves it to `QUEUED`.
5. Workforce Spine selects/claims an executor.
6. If a capability is needed, CrownGrid resolves the route outside Packet OS.
7. Execution organs produce evidence receipts and state events.
8. Implementation defects route to DEVOS.
9. `REVIEW` hands off to SECA.
10. Only SECA verification permits `VERIFIED`; only then may the packet reach `COMPLETED`.
11. Packet events mirror through the Estate Event Gateway to Runtime Observatory and proof surfaces.

## Adapter rule

External adapters translate transport details into the stable v1 packet/event/handoff contracts. They must not bypass `PacketOS` state guards.

## Idempotency and persistence

The v0.1 candidate is in-memory. Production wiring must add durable storage, event sequence numbers, idempotency keys, and optimistic concurrency before multi-worker use.
