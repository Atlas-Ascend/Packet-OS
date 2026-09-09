# 05 — Interfaces and Schemas

Minimum Packet fields: packet_id, type, title, objective, scope, source_ref, parent_refs, dependencies, priority, owner, requested_capability, constraints, permissions, inputs, acceptance_criteria, proof_class, status, created_at, updated_at, provenance.

Minimum result fields: packet_id, execution_ref, artifact_refs, test_refs, verification_ref, proof_ref, outcome, remaining_risk.

All schemas are versioned and backward compatibility is explicit.