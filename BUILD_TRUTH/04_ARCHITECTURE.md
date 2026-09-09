# 04 — Architecture

Core components:
- packet schema and validator
- packet lifecycle/state machine
- atomic dependency graph (DAG)
- storm admission controller
- weighted multi-lane scheduler
- authorization/policy binding
- assignment/routing adapter
- event emitter
- proof requirement binder
- GAQC quality governor
- reconciliation/closure service

## Canonical organ states

DRAFT, READY, ROUTED, ACTIVE, BLOCKED, VERIFY, PROVED, CLOSED, CANCELLED.

The executable Python kernel preserves the earlier proven lifecycle and exposes a compatibility mapping rather than silently rewriting history:

- DRAFT -> `DRAFT`
- READY -> `AUTHORIZED`
- ROUTED -> `QUEUED` / `CLAIMED`
- ACTIVE -> `RUNNING`
- BLOCKED -> `BLOCKED` / `FAILED`
- VERIFY -> `REVIEW`
- PROVED -> `VERIFIED`
- CLOSED -> `COMPLETED`
- CANCELLED -> `CANCELLED`

State transitions are append-only events with causal references. Mutating a packet never erases prior state.

## Atomic Packet OS v0.2

Large authorized objectives may be decomposed into atomic child packets linked through an acyclic dependency graph. `PacketGraph` rejects cycles and unknown dependencies, calculates deterministic execution waves, and releases a child only after all declared parents reach canonical CLOSED / kernel `COMPLETED` truth.

## Packet Storm

A Packet Storm is controlled parallelism, not unlimited autonomous fan-out. `PacketStorm` enforces a hard maximum packet count, bounded admission batches, dependency gates, per-lane queue limits, and per-lane concurrency ceilings.

## Work lanes

`LaneScheduler` provides weighted fair service across configurable lanes. Default lanes are research, build, integration, qa, deploy, proof, and recovery. Lane scheduling does not replace Workforce Spine worker-selection authority.

## GAQC

GAQC means Ghost Atlas Quality Control. It is the high-throughput pre-SECA quality governor for packet storms. GAQC may sample, inspect, rework, quarantine, or escalate packets, but cannot create PROVED/CLOSED (`VERIFIED`/`COMPLETED`) truth.
