# Ω / CTHULU — Packet OS Stigmergic Coordination Binding

**Canonical owner:** Atlas-Ascend/Packet-OS  
**Status:** CONTRACT PROPOSAL / NOT RUNTIME ENABLED  
**Mode:** CONVERGENCE ONLY

## Purpose

Bind Ω stigmergic coordination to Packet OS's existing packet, event, state-transition, and evidence contracts. Packet OS remains the durable shared work environment. No new queue, event bus, packet database, or coordination runtime is introduced.

## Existing contract reuse

- Packet identity and lifecycle remain governed by Packet OS packet schema and state guards.
- Packet event envelope remains contracts/event.schema.json: event_id, packet_id, event_type, source, timestamp, payload.
- Packet metadata remains the optional extension surface for mission_id, correlation_id, capability references, policy version, and coordination metadata when those values are available from their canonical issuers.
- Existing integration/ESTATE_WIRING.yaml routes packet.* events to the Estate Event Gateway; packet.queued and packet.claimed continue to connect Packet Storm and Workforce Spine.
- Existing event gateway envelope adds its required correlationId, missionId, sourceOrgan, stateClass, timestamp, and payload. Do not mint a competing correlation identity.

## Proposed event vocabulary

The following are proposed event types, not claims that the current runtime emits them:

- packet.artifact.published — a worker published a durable artifact reference.
- packet.pathway.proposed — a candidate capability relationship was recorded for owner review.
- packet.pathway.verified — an independent verification receipt qualified a relationship.
- packet.pathway.quarantined — an owner-authorized route quarantine was recorded.
- packet.signal.published — an advisory, provenance-bearing coordination signal was published.

Each event must reference a packet_id and carry a stable event_id. Payloads contain references and digests, not duplicated canonical state or secrets.

## Stigmergic worker loop

DISCOVER existing eligible packet → re-read canonical packet state → validate dependency and permission gates → claim through Workforce Spine / Packet OS existing claim contract → execute bounded work → publish artifact reference → request verification → update canonical state through Packet OS guards → expose the next eligible packet.

Event notifications are discovery hints. They do not authorize claims or state transitions. The consumer must re-read canonical packet state before acting.

## Idempotency and concurrency

Use existing event_id and packet_id; preserve mission/correlation lineage in the established envelope. Consumers deduplicate by event identity and operation idempotency key where available. Concurrent claims must use the existing Packet OS / Workforce Spine lease or claim mechanism. Do not invent a parallel lock.

## Hard boundaries

JANUS authorizes intent and material state changes. Workforce Spine selects and schedules workers. CrownGrid routes capabilities. Packet OS owns packet identity/state. DevOS and SECA retain finish truth. ProofGrid owns proof receipts. Thoth owns durable memory. Advisory signals never grant permission, trust, budget, or execution authority.

## Acceptance

Before runtime activation, add contract tests proving stale/duplicate events are harmless, unauthorized work cannot be claimed, packet state guards remain authoritative, and correlation/proof lineage survives worker handoff. A passing reference test is not live Packet OS integration proof.