# ARK Ω Runtime Binding v1.1.0 — Packet OS

Role: canonical work-envelope boundary.

Accept only commands carrying command_id, mission_id, JANUS authorization evidence, target_mode, nonce and correlation metadata. Emit packet_id and preserve command_id/mission_id unchanged through all descendants.

Required transition: AUTHORIZED -> PACKETIZED.

Fail closed on missing/invalid authority, malformed envelope, replayed nonce, or unknown target capability. No packet may be reported COMPLETE without downstream Workforce Spine receipt.

Proof fields: packet_id, parent_command_id, mission_id, created_at, policy_ref, payload_hash, dispatch_state.
