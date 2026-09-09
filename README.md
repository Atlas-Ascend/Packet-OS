# Packet OS

Packet OS is the canonical **atomic work substrate** for the Ghost Atlas estate. It turns authorized intent into bounded, stateful, evidence-bearing work packets that can move through the estate without collapsing executive authority, workforce scheduling, capability routing, or finish truth into one service.

## Position in the organism

```text
Atlas Mind / MAAT CaseGraph
          |
          v
      JANUS PRIME                 executive authorization
          |
          v
      PACKET OS                   atomic packet + state + evidence contract
       /   |   \
      v    v    v
Workforce CrownGrid Event Gateway
  Spine              |
    |                 v
    +------------> Runtime Observatory
    |
    v
MetaForge / Software Factory / distributed agents
    |
    +---- implementation failure ---> DEVOS
    |
    +---- verification request -----> SECA
                                      |
                                      v
                               Proof receipt / finish truth
```

## What Packet OS owns

- packet schema and packet identity
- lifecycle/state transition contract
- handoff envelopes
- evidence requirements and evidence receipts
- normalized packet events

## What Packet OS does **not** own

- executive authorization: JANUS
- worker selection/scheduling: Workforce Spine
- capability routing: CrownGrid
- implementation repair: DEVOS
- finish truth / quality gate: SECA

## Quick start

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m packet_os.cli demo
python -m packet_os.httpd
```

Then open `http://localhost:8080/healthz`.

## Build Truth

The ten Build Truth files under `BUILD_TRUTH/` define canon, scope, requirements, architecture, contracts, lifecycle, governance, implementation, verification, and release/operations. They are the authoritative SDLC seed for this repository.

## Integration contracts

Machine-readable schemas live in `contracts/`. Estate wiring is declared in `integration/ESTATE_WIRING.yaml` and explained in `docs/INTEGRATION.md`.

## Release posture

This branch is an **active candidate** until CI passes and SECA acceptance criteria are satisfied. No file in this repo is allowed to claim production finish truth merely because code exists.
