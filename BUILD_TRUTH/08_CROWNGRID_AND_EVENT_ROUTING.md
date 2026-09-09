# 08 — CrownGrid and Event Routing

Packet OS requests capabilities; CrownGrid resolves which organ/runtime should perform them.

Consumes events: directive.created, case.updated, defect.detected, proof.rejected, organ.degraded.

Emits: packet.created, packet.ready, packet.route_requested, packet.routed, packet.started, packet.blocked, packet.verify_requested, packet.proved, packet.closed.

Routing decisions are external to Packet OS and referenced by route receipt id.