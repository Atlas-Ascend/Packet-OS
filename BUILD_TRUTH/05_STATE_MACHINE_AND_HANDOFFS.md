# BUILD TRUTH 05 — State Machine and Handoffs

## States

`DRAFT -> AUTHORIZED -> QUEUED -> CLAIMED -> RUNNING -> REVIEW -> VERIFIED -> COMPLETED`

Exceptional states: `BLOCKED`, `FAILED`, `CANCELLED`.

## Core rules

- DRAFT may be cancelled or externally authorized.
- AUTHORIZED may be queued or cancelled.
- QUEUED may be claimed, blocked, or cancelled.
- CLAIMED may run, block, or cancel.
- RUNNING may review, block, or fail.
- BLOCKED may return to queue/claim, fail, or cancel.
- REVIEW may verify, return to running, or fail.
- VERIFIED may complete or return to running if verification is invalidated.
- FAILED may be requeued after remediation or cancelled.
- COMPLETED/CANCELLED are terminal.

## Canonical handoff chain

`JANUS authorization -> Packet OS normalization -> Workforce Spine claim -> execution organ -> Packet OS REVIEW -> SECA VERIFIED -> COMPLETED/proof receipt`.

Capability requests may branch through CrownGrid. Implementation defects branch to DEVOS and re-enter through `FAILED/BLOCKED -> QUEUED` only with a recorded transition.
