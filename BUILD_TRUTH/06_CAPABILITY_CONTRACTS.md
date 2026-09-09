# 06 — Capability Contracts

Packet OS exposes:
- packet.create
- packet.validate
- packet.split
- packet.link
- packet.ready
- packet.route_request
- packet.transition
- packet.block
- packet.verify_request
- packet.prove
- packet.close
- packet.reconcile

Capabilities require authenticated caller context and declared authority. Transition operations reject invalid state movement or missing required evidence.