# Atomic Packet OS v2 — GAQC Packet Storm

## Canonical definition

Atomic Packet OS v2 is the governed parallel work substrate for the Ghost Atlas estate. A large objective is represented as a dependency graph of atomic packets, admitted into bounded work lanes, executed by the Workforce, quality-intercepted by GAQC, verified by SECA, and closed through evidence receipts.

GAQC means **Ghost Atlas Quality Control**. GAQC is not a replacement for SECA. It is the high-throughput pre-verification quality governor for packet storms.

## Operating model

```text
Atlas Mind / MAAT / operator intent
              |
              v
          JANUS PRIME
      executive authorization
              |
              v
      Atomic Packet Graph
     DAG + waves + dependencies
              |
              v
      Storm Admission Control
   max fanout + batch + backpressure
              |
              v
+-------------+-------------+-------------+
| research    | build       | integration |
| QA          | deploy      | proof       |
| recovery    | custom lanes as declared |
+-------------+-------------+-------------+
              |
              v
            GAQC
 risk sampling / evidence completeness /
 defect classification / quarantine
       |              |             |
       |              |             +--> JANUS critical escalation
       |              +----------------> DEVOS rework
       +-------------------------------> SECA verification
                                              |
                                              v
                                         ProofGrid truth
```

## Atomic packet invariant

An atomic packet must have one bounded objective, explicit acceptance criteria, an evidence contract, a work lane, a risk class, a stable idempotency key, and dependency references. A packet may be retried, re-routed, or quarantined, but its identity and evidence lineage remain stable.

## Packet graph

`PacketGraph` is a cycle-rejecting DAG. It provides:

- dependency validation;
- deterministic topological order;
- parallel execution waves;
- ready-set calculation;
- critical-path length;
- explicit prevention of dependency fanout over unknown packets.

Dependencies unlock only after upstream packets reach canonical `COMPLETED`. Merely running or passing GAQC does not unlock downstream work.

## Work lanes

`LaneScheduler` uses weighted fair rotation with lane-local concurrency limits and bounded queues. Lanes are execution classes, not authority classes.

Default lanes:

| lane | concurrency | weight | purpose |
| --- | ---: | ---: | --- |
| research | 4 | 2 | investigation, analysis, discovery |
| build | 8 | 4 | primary implementation throughput |
| integration | 4 | 2 | wiring, adapters, convergence |
| qa | 4 | 3 | tests, inspection, GAQC work |
| deploy | 2 | 1 | release/deployment operations |
| proof | 4 | 2 | SECA/ProofGrid evidence work |
| recovery | 2 | 1 | DEVOS repair and failed-packet recovery |

All lane values are configuration defaults, not hard-coded estate limits.

## Backpressure

Packet Storm refuses uncontrolled fanout through three controls:

1. `max_packets` — hard storm-size ceiling;
2. `admission_batch` — bounds each ready-set admission wave;
3. `queue_limit` + `concurrency` — bounds each work lane.

When a lane is saturated, admission records a backpressure event and leaves the packet authorized but unqueued. Work is not dropped.

## GAQC policy

GAQC applies deterministic risk sampling so repeated evaluation of the same `storm_id + packet_id` yields the same inspection decision.

Default inspection rates:

- LOW: 10%
- MEDIUM: 35%
- HIGH: 100%
- CRITICAL: 100%

GAQC dispositions:

- `BYPASS_TO_SECA` — GAQC sampling skipped; SECA remains mandatory;
- `PASS_TO_SECA` — inspection clean; route to SECA;
- `REWORK` — evidence or quality deficiency; route to DEVOS;
- `QUARANTINE` — high-severity defect; hold and route to SECA;
- `ESCALATE` — critical defect; route to JANUS.

GAQC never invokes `verify_packet()` as itself and never owns `COMPLETED` truth.

## Storm telemetry

Every `PacketStorm.snapshot()` exposes:

- packet count;
- critical-path length;
- execution waves;
- packet state distribution;
- per-lane queue/in-flight/capacity telemetry;
- created/admitted/claimed/completed counts;
- GAQC pass/rework/quarantine/escalation counts;
- backpressure events.

This surface is intended for Runtime Observatory, JANUS VIBE, ProofGrid, and operational dashboards.

## Estate authority boundaries

- JANUS: executive authorization and critical escalation resolution.
- Packet OS: atomic identity, state, dependency graph, lane admission, handoff/evidence contracts.
- Workforce Spine: worker selection, assignment policy, worker lifecycle.
- CrownGrid: capability and I/O routing.
- GAQC: high-throughput pre-SECA quality interception.
- DEVOS: implementation remediation and recovery.
- SECA: acceptance gates, verification, finish truth.
- ProofGrid: durable proof receipts and proof presentation.

## Definition of done for v2 source promotion

1. legacy Packet OS v0.1 lifecycle tests remain green;
2. DAG cycle/unknown dependency tests pass;
3. weighted multi-lane scheduling tests pass;
4. queue limits and lane concurrency enforce backpressure;
5. a 100-packet storm admits all eligible packets while claiming only available execution capacity;
6. missing evidence routes to DEVOS;
7. critical defects route to JANUS;
8. GAQC cannot verify a packet;
9. SECA remains required before `COMPLETED`;
10. Docker build remains green.
