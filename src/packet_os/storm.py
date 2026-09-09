from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .atomic import AtomicPacketSpec, PacketGraph, RiskLevel
from .gaqc import GAQCDecision, GAQCDisposition, GAQCGovernor, QualityDefect
from .lanes import BackpressureError, LaneScheduler, WorkLane, standard_lanes
from .models import Packet, PacketState
from .service import PacketOS


@dataclass(frozen=True, slots=True)
class StormConfig:
    max_packets: int = 10_000
    admission_batch: int = 512

    def __post_init__(self) -> None:
        if self.max_packets < 1:
            raise ValueError("max_packets must be >= 1")
        if self.admission_batch < 1:
            raise ValueError("admission_batch must be >= 1")


@dataclass(slots=True)
class StormMetrics:
    created: int = 0
    admitted: int = 0
    claimed: int = 0
    completed: int = 0
    quality_pass: int = 0
    quality_rework: int = 0
    quarantined: int = 0
    escalated: int = 0
    backpressure_events: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "created": self.created,
            "admitted": self.admitted,
            "claimed": self.claimed,
            "completed": self.completed,
            "quality_pass": self.quality_pass,
            "quality_rework": self.quality_rework,
            "quarantined": self.quarantined,
            "escalated": self.escalated,
            "backpressure_events": self.backpressure_events,
        }


class PacketStorm:
    """Controlled parallel execution fabric over canonical Packet OS packets."""

    def __init__(
        self,
        specs: list[AtomicPacketSpec],
        *,
        packet_os: PacketOS | None = None,
        lanes: list[WorkLane] | None = None,
        gaqc: GAQCGovernor | None = None,
        config: StormConfig | None = None,
        storm_id: str | None = None,
    ) -> None:
        self.graph = PacketGraph(specs)
        self.config = config or StormConfig()
        if len(self.graph.specs) > self.config.max_packets:
            raise ValueError(f"packet storm exceeds max_packets={self.config.max_packets}")
        self.packet_os = packet_os or PacketOS()
        self.scheduler = LaneScheduler(lanes or standard_lanes())
        self.gaqc = gaqc or GAQCGovernor()
        self.storm_id = storm_id or f"storm-{uuid4()}"
        self.packet_by_key: dict[str, str] = {}
        self.key_by_packet: dict[str, str] = {}
        self.admitted: set[str] = set()
        self.completed_keys: set[str] = set()
        self.metrics = StormMetrics()

        unknown_lanes = sorted({spec.lane for spec in self.graph.specs.values()} - set(self.scheduler.lanes))
        if unknown_lanes:
            raise ValueError("storm references unknown lanes: " + ", ".join(unknown_lanes))

    def seed(self) -> dict[str, Packet]:
        if self.packet_by_key:
            return {key: self.packet_os.packets[packet_id] for key, packet_id in self.packet_by_key.items()}

        for key in self.graph.topological_order():
            spec = self.graph.specs[key]
            packet = self.packet_os.create_packet(
                objective=spec.objective,
                source=f"GAQC_PACKET_STORM:{self.storm_id}",
                acceptance_criteria=list(spec.acceptance_criteria),
                evidence_requirements=list(spec.evidence_requirements),
                priority=spec.priority,
                constraints=list(spec.constraints),
                metadata={
                    **spec.metadata,
                    "storm_id": self.storm_id,
                    "atomic_key": key,
                    "lane": spec.lane,
                    "depends_on": list(spec.depends_on),
                    "risk": spec.risk.value,
                    "idempotency_key": spec.idempotency_key or f"{self.storm_id}:{key}",
                },
            )
            self.packet_by_key[key] = packet.packet_id
            self.key_by_packet[packet.packet_id] = key
            self.metrics.created += 1
        return {key: self.packet_os.packets[packet_id] for key, packet_id in self.packet_by_key.items()}

    def authorize_all(self, *, authority: str, authorization_ref: str) -> None:
        self.seed()
        for key in self.graph.topological_order():
            packet_id = self.packet_by_key[key]
            packet = self.packet_os.packets[packet_id]
            if packet.state is PacketState.DRAFT:
                self.packet_os.authorize(
                    packet_id,
                    authority=authority,
                    authorization_ref=f"{authorization_ref}:{key}",
                )

    def admit_ready(self) -> tuple[str, ...]:
        ready = self.graph.ready(self.completed_keys, self.admitted)
        admitted_now: list[str] = []
        for key in ready[: self.config.admission_batch]:
            packet_id = self.packet_by_key[key]
            packet = self.packet_os.packets[packet_id]
            if packet.state is not PacketState.AUTHORIZED:
                continue
            spec = self.graph.specs[key]
            try:
                self.scheduler.enqueue(packet_id, spec.lane)
            except BackpressureError:
                self.metrics.backpressure_events += 1
                continue
            self.packet_os.transition(packet_id, PacketState.QUEUED, actor="PacketStorm", note=f"admitted to lane {spec.lane}")
            self.admitted.add(key)
            admitted_now.append(key)
            self.metrics.admitted += 1
        return tuple(admitted_now)

    def claim_next(self, *, worker: str) -> Packet | None:
        claimed = self.scheduler.claim_next()
        if claimed is None:
            return None
        lane_name, packet_id = claimed
        packet = self.packet_os.claim(packet_id, worker=worker)
        packet.metadata["claimed_lane"] = lane_name
        self.metrics.claimed += 1
        return packet

    def start(self, packet_id: str, *, actor: str) -> Packet:
        return self.packet_os.transition(packet_id, PacketState.RUNNING, actor=actor, note="atomic execution started")

    def submit_for_review(self, packet_id: str, *, actor: str) -> Packet:
        packet = self.packet_os.transition(packet_id, PacketState.REVIEW, actor=actor, note="execution submitted for quality review")
        self.scheduler.release(packet_id)
        return packet

    def inspect_quality(
        self,
        packet_id: str,
        *,
        defects: tuple[QualityDefect, ...] = (),
    ) -> GAQCDecision:
        packet = self.packet_os.packets[packet_id]
        if packet.state is not PacketState.REVIEW:
            raise ValueError("GAQC inspection requires packet state REVIEW")
        risk = RiskLevel(str(packet.metadata.get("risk", RiskLevel.MEDIUM.value)))
        decision = self.gaqc.inspect(
            storm_id=self.storm_id,
            packet=packet,
            risk=risk,
            defects=defects,
        )
        packet.metadata["gaqc"] = {
            "inspected": decision.inspected,
            "disposition": decision.disposition.value,
            "reasons": list(decision.reasons),
            "missing_evidence": list(decision.missing_evidence),
        }
        if decision.disposition in {GAQCDisposition.PASS_TO_SECA, GAQCDisposition.BYPASS_TO_SECA}:
            self.metrics.quality_pass += 1
            self.packet_os.handoff(packet_id, source="GAQC", target="SECA", reason=decision.disposition.value)
        elif decision.disposition is GAQCDisposition.REWORK:
            self.metrics.quality_rework += 1
            self.packet_os.handoff(packet_id, source="GAQC", target="DEVOS", reason="quality rework required")
        elif decision.disposition is GAQCDisposition.QUARANTINE:
            self.metrics.quarantined += 1
            self.packet_os.handoff(packet_id, source="GAQC", target="SECA", reason="quality quarantine")
        elif decision.disposition is GAQCDisposition.ESCALATE:
            self.metrics.escalated += 1
            self.packet_os.handoff(packet_id, source="GAQC", target="JANUS", reason="critical quality escalation")
        return decision

    def seca_verify(self, packet_id: str, *, actor: str = "SECA") -> Packet:
        return self.packet_os.verify_packet(packet_id, actor=actor)

    def complete(self, packet_id: str, *, actor: str) -> Packet:
        packet = self.packet_os.complete_packet(packet_id, actor=actor)
        key = self.key_by_packet[packet_id]
        self.completed_keys.add(key)
        self.metrics.completed += 1
        self.admit_ready()
        return packet

    def snapshot(self) -> dict[str, object]:
        states: dict[str, int] = {}
        for packet_id in self.packet_by_key.values():
            state = self.packet_os.packets[packet_id].state.value
            states[state] = states.get(state, 0) + 1
        return {
            "storm_id": self.storm_id,
            "packet_count": len(self.packet_by_key),
            "critical_path_length": self.graph.critical_path_length(),
            "waves": [list(wave) for wave in self.graph.waves()],
            "states": states,
            "lanes": self.scheduler.metrics(),
            "metrics": self.metrics.to_dict(),
        }
