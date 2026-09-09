# 04 — Architecture

Core components:
- packet schema and validator
- packet lifecycle/state machine
- dependency graph
- authorization/policy binding
- assignment/routing adapter
- event emitter
- proof requirement binder
- reconciliation/closure service

Canonical states: DRAFT, READY, ROUTED, ACTIVE, BLOCKED, VERIFY, PROVED, CLOSED, CANCELLED.

State transitions are append-only events with causal references. Mutating a packet never erases prior state.