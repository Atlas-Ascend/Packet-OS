# 07 — Packet OS Integration

This repository is the canonical Packet OS implementation boundary. All estate organs consuming work should accept a packet envelope or an adapter that preserves packet_id, objective, constraints, provenance, proof requirements, storm identity when present, and parent/child dependency references.

No downstream organ may silently discard packet identity. Child work produces child packet IDs linked to the parent. Completion returns upstream as a structured result, never only prose.

## Atomic storm integration

A large authorized objective may become a `PacketGraph` of atomic packets. Packet OS owns the graph and bounded admission semantics, not worker choice or capability routing.

Canonical handoff:

`JANUS authorization -> PacketGraph -> PacketStorm admission -> Workforce Spine claim -> execution organ -> REVIEW -> GAQC -> SECA -> ProofGrid -> upstream reconciliation`.

## Multiple work lanes

Packet Storm may place ready atoms into research, build, integration, qa, deploy, proof, recovery, or explicitly declared custom lanes. LaneScheduler controls queue/concurrency capacity only. Workforce Spine remains authoritative for which worker performs the claimed packet.

## Backpressure

If a target lane is saturated, the packet remains durable and authorized but is not silently dropped or force-claimed. Packet Storm records a backpressure event and retries admission when capacity exists.

## GAQC integration

GAQC is an internal Packet OS quality governor and may produce:

- `BYPASS_TO_SECA`
- `PASS_TO_SECA`
- `REWORK` -> DEVOS
- `QUARANTINE` -> SECA
- `ESCALATE` -> JANUS

A GAQC pass never substitutes for SECA verification.
