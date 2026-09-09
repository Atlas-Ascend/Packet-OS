# BUILD TRUTH 04 — Data Contracts

## Packet

Required semantic fields: `packet_id`, `objective`, `source`, `priority`, `state`, timestamps, `acceptance_criteria`, `evidence_requirements`, `evidence`, `authorization_ref`, `assigned_to`, constraints, metadata, history.

## Evidence receipt

An evidence receipt binds `packet_id`, `kind`, `uri`, `digest`, `producer`, timestamp, and optional claims. The digest is content-addressable metadata; Packet OS does not pretend a URI alone proves correctness.

## Packet event

Every mutation emits an event with `event_id`, `packet_id`, `event_type`, source, optional target, timestamp, and payload.

## Handoff envelope

A handoff must state source, target, reason, packet ID, and contract version. A handoff transfers responsibility for the next operation; it does not transfer governance authority outside the target's contract.

## Versioning

Schemas in `contracts/` are `v1`. Breaking changes require a new schema version and an explicit migration path.
