# BUILD TRUTH 02 — Requirements and Acceptance

## Functional requirements

- **R1** Create a packet with globally unique ID, objective, source, acceptance criteria, constraints, priority, and evidence requirements.
- **R2** Capture external authorization before entering `AUTHORIZED`.
- **R3** Enforce an explicit state-transition graph.
- **R4** Emit a normalized event for every lifecycle mutation.
- **R5** Attach evidence receipts with producer, URI, digest, kind, timestamp, and claims.
- **R6** Block verification when required evidence kinds are missing.
- **R7** Permit verification only by configured verification authority.
- **R8** Permit completion only from `VERIFIED`.
- **R9** Export JSON-safe packet/event/evidence objects.
- **R10** Expose health and capability metadata without external dependencies.

## Non-functional requirements

- Python 3.11+
- standard-library runtime
- deterministic canonical JSON hashing
- no shell execution surface
- no embedded credentials
- no self-promotion or self-merge semantics
- tests runnable with `unittest`

## Acceptance criteria

The candidate is releasable when CI proves: import/compile success, unit tests pass, CLI happy-path demo completes, Docker image builds, and the SECA gate checklist is satisfied.
