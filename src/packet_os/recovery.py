from __future__ import annotations

from .models import EvidenceRequirement, Packet
from .service import PacketOS

OSIRIS_RECOVERY_CAPABILITY = "estate.recovery.route"

RECOVERY_EVIDENCE = [
    EvidenceRequirement(kind="checkpoint", description="Thoth checkpoint source and digest"),
    EvidenceRequirement(kind="execution", description="Attributed bounded recovery execution result"),
    EvidenceRequirement(kind="seca-verification", description="Independent SECA recovery verdict"),
    EvidenceRequirement(kind="proofgrid", description="ProofGrid recovery receipt"),
    EvidenceRequirement(kind="thoth-post-checkpoint", description="Post-recovery Thoth lineage checkpoint"),
]


def create_osiris_recovery_packet(
    packet_os: PacketOS,
    *,
    checkpoint_id: str,
    target: str,
    reason: str,
    source: str = "Ghost-Atlas-Control-Plane",
    priority: int = 90,
) -> Packet:
    """Create the canonical bounded Packet OS work item for an OSIRIS recovery.

    This function creates work identity only. It does not authorize, execute,
    verify, or promote recovery on its own.
    """

    if not checkpoint_id.strip():
        raise ValueError("checkpoint_id is required")
    if not target.strip():
        raise ValueError("recovery target is required")
    if not reason.strip():
        raise ValueError("recovery reason is required")

    return packet_os.create_packet(
        objective=f"Recover {target} from evidence-backed checkpoint {checkpoint_id}",
        source=source,
        acceptance_criteria=[
            "checkpoint lineage is preserved",
            "recovery action is bounded and attributable",
            "SECA independently verifies the recovered target",
            "ProofGrid issues a recovery receipt",
            "Thoth records a post-recovery checkpoint without erasing the failed state",
        ],
        evidence_requirements=list(RECOVERY_EVIDENCE),
        priority=priority,
        constraints=[
            "NO_REPLACEMENT_BUILD",
            "NO_SOURCE_HISTORY_REWRITE",
            "JANUS_AUTHORIZATION_REQUIRED_BEFORE_EXECUTION",
            "MEDUSA_HEIMDALL_MAY_DENY_OR_QUARANTINE",
            "EXECUTOR_MAY_NOT_SELF_VERIFY",
            "RECOVERY_MUST_CLOSE_BACK_TO_THOTH",
        ],
        inputs={
            "checkpoint_id": checkpoint_id,
            "recovery_target": target,
            "recovery_reason": reason,
        },
        metadata={
            "capability_id": OSIRIS_RECOVERY_CAPABILITY,
            "recovery_role": "OSIRIS-RECOVERY",
            "memory_owner": "THOTH",
            "verification_authority": packet_os.verification_authority,
        },
    )
