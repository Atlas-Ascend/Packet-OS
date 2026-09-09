# BUILD TRUTH 03 — Architecture

## Layers

1. **Contract layer** — dataclasses/enums and JSON schemas.
2. **State layer** — legal transition graph and transition guard.
3. **Evidence layer** — canonical digesting and evidence receipts.
4. **Event layer** — normalized packet events and in-process event bus.
5. **Service layer** — PacketOS use cases and authority checks.
6. **Adapter layer** — CLI/HTTP health and future estate transports.
7. **Proof layer** — Build Truth, CI, SECA checklist, release receipt.

## Runtime shape

Packet OS is intentionally transport-agnostic. The v0.1 kernel runs in-process and exposes a minimal HTTP health/capability surface. Production transports can bind the same packet/event contracts to the Estate Event Gateway, Workforce Spine, CrownGrid, or service mesh without changing the core state machine.

## Failure domains

- invalid implementation/state mutation -> reject locally and route incident to DEVOS when external repair is required
- missing/invalid evidence -> remain in REVIEW or return to RUNNING
- quality/finish ambiguity -> SECA gate
- worker unavailable -> Workforce Spine concern
- capability unavailable -> CrownGrid concern
