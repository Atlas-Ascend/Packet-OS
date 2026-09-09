from __future__ import annotations

from typing import Any

from .bus import EventBus
from .evidence import make_receipt
from .models import EvidenceRequirement, HandoffEnvelope, Packet, PacketEvent, PacketState, utc_now
from .state_machine import assert_transition


class PacketOS:
    def __init__(self, *, verification_authority: str = "SECA", bus: EventBus | None = None) -> None:
        self.verification_authority = verification_authority
        self.bus = bus or EventBus()
        self.packets: dict[str, Packet] = {}

    def create_packet(
        self,
        *,
        objective: str,
        source: str,
        acceptance_criteria: list[str],
        evidence_requirements: list[EvidenceRequirement],
        priority: int = 50,
        constraints: list[str] | None = None,
        inputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Packet:
        packet = Packet(
            objective=objective,
            source=source,
            acceptance_criteria=acceptance_criteria,
            evidence_requirements=evidence_requirements,
            priority=priority,
            constraints=constraints or [],
            inputs=inputs or {},
            metadata=metadata or {},
        )
        packet.validate()
        packet.history.append({"state": packet.state.value, "actor": source, "timestamp": packet.created_at, "note": "created"})
        self.packets[packet.packet_id] = packet
        self._emit(packet, "packet.created", source, {"state": packet.state.value})
        return packet

    def authorize(self, packet_id: str, *, authority: str, authorization_ref: str) -> Packet:
        packet = self._get(packet_id)
        if not authority.strip() or not authorization_ref.strip():
            raise ValueError("external authority and authorization_ref are required")
        packet.authorization_ref = authorization_ref
        packet.metadata["authorized_by"] = authority
        return self._transition(packet, PacketState.AUTHORIZED, authority, "external authorization recorded")

    def transition(self, packet_id: str, target: PacketState, *, actor: str, note: str = "") -> Packet:
        if target is PacketState.VERIFIED:
            raise PermissionError("use verify_packet(); verification is a governed operation")
        packet = self._get(packet_id)
        return self._transition(packet, target, actor, note)

    def claim(self, packet_id: str, *, worker: str) -> Packet:
        packet = self._get(packet_id)
        packet.assigned_to = worker
        return self._transition(packet, PacketState.CLAIMED, worker, "workforce claim")

    def attach_evidence(
        self,
        packet_id: str,
        *,
        kind: str,
        uri: str,
        producer: str,
        payload: Any,
        claims: dict[str, Any] | None = None,
    ):
        packet = self._get(packet_id)
        receipt = make_receipt(packet_id=packet_id, kind=kind, uri=uri, producer=producer, payload=payload, claims=claims)
        packet.evidence.append(receipt)
        packet.updated_at = utc_now()
        self._emit(packet, "packet.evidence.attached", producer, {"evidence": receipt.to_dict()})
        return receipt

    def verify_packet(self, packet_id: str, *, actor: str) -> Packet:
        packet = self._get(packet_id)
        if actor != self.verification_authority:
            raise PermissionError(f"verification authority is {self.verification_authority}")
        required = {r.kind for r in packet.evidence_requirements if r.required}
        present = {e.kind for e in packet.evidence}
        missing = sorted(required - present)
        if missing:
            raise ValueError("missing required evidence: " + ", ".join(missing))
        return self._transition(packet, PacketState.VERIFIED, actor, "verification gate passed")

    def complete_packet(self, packet_id: str, *, actor: str) -> Packet:
        packet = self._get(packet_id)
        return self._transition(packet, PacketState.COMPLETED, actor, "completed after verification")

    def handoff(self, packet_id: str, *, source: str, target: str, reason: str) -> HandoffEnvelope:
        packet = self._get(packet_id)
        envelope = HandoffEnvelope(packet_id=packet_id, source=source, target=target, reason=reason)
        self._emit(packet, "packet.handoff", source, {"handoff": envelope.to_dict()}, target=target)
        return envelope

    def _transition(self, packet: Packet, target: PacketState, actor: str, note: str) -> Packet:
        assert_transition(packet.state, target)
        previous = packet.state
        packet.state = target
        packet.updated_at = utc_now()
        packet.validate()
        packet.history.append({"from": previous.value, "state": target.value, "actor": actor, "timestamp": packet.updated_at, "note": note})
        self._emit(packet, "packet.state.changed", actor, {"from": previous.value, "to": target.value, "note": note})
        return packet

    def _emit(self, packet: Packet, event_type: str, source: str, payload: dict[str, Any], target: str | None = None) -> None:
        self.bus.publish(PacketEvent(packet_id=packet.packet_id, event_type=event_type, source=source, target=target, payload=payload))

    def _get(self, packet_id: str) -> Packet:
        try:
            return self.packets[packet_id]
        except KeyError as exc:
            raise KeyError(f"unknown packet: {packet_id}") from exc
