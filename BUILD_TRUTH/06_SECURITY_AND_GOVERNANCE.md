# BUILD TRUTH 06 — Security and Governance

## Authority boundaries

Packet OS records authority; it does not manufacture it. `authorize()` requires an external authority identifier and authorization reference. `verify_packet()` requires the configured verification authority, default `SECA`.

## Prohibited behavior

- arbitrary shell execution
- secret storage in packet payloads
- hidden state mutation
- bypassing illegal transitions
- self-verification
- completion without verification
- worker or capability selection masquerading as packet bookkeeping

## Data handling

Packet metadata should contain references, not raw credentials or private secrets. Sensitive payload transport belongs behind Medusa/security policy and estate secret management.

## Auditability

History and events are append-only at the service-contract level. Production persistence must preserve event order and packet identity.
