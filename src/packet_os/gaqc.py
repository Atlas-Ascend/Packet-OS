from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

from .atomic import RiskLevel
from .models import Packet


class GAQCDisposition(str, Enum):
    BYPASS_TO_SECA = "BYPASS_TO_SECA"
    PASS_TO_SECA = "PASS_TO_SECA"
    REWORK = "REWORK"
    QUARANTINE = "QUARANTINE"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True, slots=True)
class QualityDefect:
    code: str
    severity: RiskLevel
    detail: str = ""


@dataclass(frozen=True, slots=True)
class GAQCDecision:
    inspected: bool
    disposition: GAQCDisposition
    reasons: tuple[str, ...]
    missing_evidence: tuple[str, ...] = ()
    defects: tuple[QualityDefect, ...] = ()


@dataclass(frozen=True, slots=True)
class GAQCPolicy:
    low_sample_rate: float = 0.10
    medium_sample_rate: float = 0.35
    high_sample_rate: float = 1.0
    critical_sample_rate: float = 1.0

    def sample_rate(self, risk: RiskLevel) -> float:
        return {
            RiskLevel.LOW: self.low_sample_rate,
            RiskLevel.MEDIUM: self.medium_sample_rate,
            RiskLevel.HIGH: self.high_sample_rate,
            RiskLevel.CRITICAL: self.critical_sample_rate,
        }[risk]


class GAQCGovernor:
    """Ghost Atlas Quality Control pre-SECA quality interception.

    GAQC can inspect and route. It cannot create VERIFIED/COMPLETED truth.
    """

    def __init__(self, policy: GAQCPolicy | None = None) -> None:
        self.policy = policy or GAQCPolicy()

    def should_inspect(self, *, storm_id: str, packet_id: str, risk: RiskLevel) -> bool:
        rate = self.policy.sample_rate(risk)
        if rate >= 1:
            return True
        if rate <= 0:
            return False
        digest = sha256(f"{storm_id}:{packet_id}".encode()).digest()
        value = int.from_bytes(digest[:8], "big") / ((1 << 64) - 1)
        return value < rate

    def inspect(
        self,
        *,
        storm_id: str,
        packet: Packet,
        risk: RiskLevel,
        defects: tuple[QualityDefect, ...] = (),
    ) -> GAQCDecision:
        inspected = self.should_inspect(storm_id=storm_id, packet_id=packet.packet_id, risk=risk)
        if not inspected:
            return GAQCDecision(
                inspected=False,
                disposition=GAQCDisposition.BYPASS_TO_SECA,
                reasons=("deterministic risk sample bypassed GAQC; SECA still required",),
            )

        required = {requirement.kind for requirement in packet.evidence_requirements if requirement.required}
        present = {receipt.kind for receipt in packet.evidence}
        missing = tuple(sorted(required - present))

        if any(defect.severity is RiskLevel.CRITICAL for defect in defects):
            return GAQCDecision(
                inspected=True,
                disposition=GAQCDisposition.ESCALATE,
                reasons=("critical quality defect",),
                missing_evidence=missing,
                defects=defects,
            )
        if any(defect.severity is RiskLevel.HIGH for defect in defects):
            return GAQCDecision(
                inspected=True,
                disposition=GAQCDisposition.QUARANTINE,
                reasons=("high-severity quality defect",),
                missing_evidence=missing,
                defects=defects,
            )
        if defects or missing:
            return GAQCDecision(
                inspected=True,
                disposition=GAQCDisposition.REWORK,
                reasons=tuple(
                    reason
                    for reason in (
                        "quality defect present" if defects else "",
                        "required evidence missing" if missing else "",
                    )
                    if reason
                ),
                missing_evidence=missing,
                defects=defects,
            )
        return GAQCDecision(
            inspected=True,
            disposition=GAQCDisposition.PASS_TO_SECA,
            reasons=("GAQC inspection passed; SECA finish truth still required",),
        )
