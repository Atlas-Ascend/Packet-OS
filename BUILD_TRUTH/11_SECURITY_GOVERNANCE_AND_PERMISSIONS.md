# 11 — Security, Governance, and Permissions

Packet creation does not imply execution authority. Each packet binds requested permissions, allowed capabilities, destructive-action flags, data sensitivity, and escalation requirements.

Denied by default: arbitrary shell, secret access, destructive mutation, policy bypass, self-promotion, and proof substitution unless a governed capability explicitly authorizes them.

Medusa/HEIMDALL may quarantine or deny work; JANUS resolves authorized escalations.