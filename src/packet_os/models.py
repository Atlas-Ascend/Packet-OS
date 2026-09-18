from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


APF_SOURCE = "JANUS-ATLAS-PROMPT-FABRIC"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PacketState(str, Enum):
    DRAFT = "DRAFT"
    AUTHORIZED = "AUTHORIZED"
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True)
class EvidenceRequirement:
    kind: str
    description: str
    required: bool = True


@dataclass(slots=True)
class EvidenceReceipt:
    packet_id: str
    kind: str
    uri: str
    digest: str
    producer: str
    claims: dict[str, Any] = field(default_factory=dict)
    evidence_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HandoffEnvelope:
    packet_id: str
    source: str
    target: str
    reason: str
    contract_version: str = "v1"
    handoff_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PacketEvent:
    packet_id: str
    event_type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    target: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Packet:
    objective: str
    source: str
    acceptance_criteria: list[str]
    evidence_requirements: list[EvidenceRequirement]
    priority: int = 50
    constraints: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    packet_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None
    run_id: str | None = None
    attempt: int = 1
    requested_by: str | None = None
    capability_request: str | None = None
    request_digest: str | None = None
    policy_snapshot_digest: str | None = None
    authorization_expires_at: str | None = None
    state: PacketState = PacketState.DRAFT
    authorization_ref: str | None = None
    assigned_to: str | None = None
    evidence: list[EvidenceReceipt] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        if not self.packet_id.strip():
            raise ValueError("packet_id is required")
        if not self.objective.strip():
            raise ValueError("packet objective is required")
        if not self.source.strip():
            raise ValueError("packet source is required")
        if not self.acceptance_criteria:
            raise ValueError("at least one acceptance criterion is required")
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")
        if self.attempt < 1:
            raise ValueError("attempt must be >= 1")
        if self.source == APF_SOURCE:
            required = {
                "correlation_id": self.correlation_id,
                "run_id": self.run_id,
                "requested_by": self.requested_by,
                "capability_request": self.capability_request,
                "request_digest": self.request_digest,
                "policy_snapshot_digest": self.policy_snapshot_digest,
                "authorization_expires_at": self.authorization_expires_at,
            }
            missing = [name for name, value in required.items() if not isinstance(value, str) or not value.strip()]
            if missing:
                raise ValueError("APF packet missing required admission identity: " + ", ".join(sorted(missing)))
        if self.state is not PacketState.DRAFT and not self.authorization_ref:
            raise ValueError("non-draft packet requires authorization_ref")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data
