# 07 — Packet OS Integration

This repository is the canonical Packet OS implementation boundary. All estate organs consuming work should accept a packet envelope or an adapter that preserves packet_id, objective, constraints, provenance, and proof requirements.

No downstream organ may silently discard the packet identity. Child work produces child packet ids linked to the parent.

Completion returns upstream as a structured result, never only prose.