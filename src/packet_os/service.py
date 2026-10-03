from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from .bus import EventBus
from .evidence import make_receipt
from .models import APF_SOURCE, EvidenceRequirement, HandoffEnvelope, Packet, PacketEvent, PacketState, utc_now
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
        packet_id: str | None = None,
        correlation_id: str | None = None,
        run_id: str | None = None,
        attempt: int = 1,
        requested_by: str | None = None,
        capability_request: str | None = None,
        request_digest: str | None = None,
        policy_snapshot_digest: str | None = None,
        authorization_expires_at: str | None = None,
    ) -> Packet:
        packet_kwargs: dict[str, Any] = {
            "objective": objective,
            "source": source,
            "acceptance_criteria": acceptance_criteria,
            "evidence_requirements": evidence_requirements,
            "priority": priority,
            "constraints": constraints or [],
            "inputs": inputs or {},
            "metadata": metadata or {},
            "correlation_id": correlation_id,
            "run_id": run_id,
            "attempt": attempt,
            "requested_by": requested_by,
            "capability_request": capability_request,
            "request_digest": request_digest,
            "policy_snapshot_digest": policy_snapshot_digest,
            "authorization_expires_at": authorization_expires_at,
        }
        if packet_id is not None:
            packet_kwargs["packet_id"] = packet_id
        elif source == APF_SOURCE:
            raise ValueError("APF packet_id must be supplied by the producer and preserved")

        packet = Packet(**packet_kwargs)
        packet.validate()
        packet.history.append({"state": packet.state.value, "actor": source, "timestamp": packet.created_at, "note": "created"})
        self.packets[packet.packet_id] = packet
        self._emit(packet, "packet.created", source, {"state": packet.state.value})
        return packet

    def authorize(
        self,
        packet_id: str,
        *,
        authority: str,
        authorization_ref: str,
        authorization_receipt: dict[str, Any] | None = None,
    ) -> Packet:
        packet = self._get(packet_id)
        if not authority.strip() or not authorization_ref.strip():
            raise ValueError("external authority and authorization_ref are required")
        if packet.source == APF_SOURCE:
            receipt_digest = self._validate_apf_authorization_receipt(
                packet,
                authority=authority,
                authorization_ref=authorization_ref,
                authorization_receipt=authorization_receipt,
            )
            packet.metadata["authorization_receipt_digest"] = receipt_digest
            packet.metadata["authorization_proof"] = "JANUS_RECEIPT_VERIFIED"
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

    def _validate_apf_authorization_receipt(
        self,
        packet: Packet,
        *,
        authority: str,
        authorization_ref: str,
        authorization_receipt: dict[str, Any] | None,
    ) -> str:
        if not isinstance(authorization_receipt, dict):
            raise ValueError("APF authorization requires the exact JANUS authorization receipt")

        receipt = authorization_receipt
        admission = receipt.get("admission")
        handoff = receipt.get("handoff")
        validity = receipt.get("validity")
        if not isinstance(admission, dict) or not isinstance(handoff, dict) or not isinstance(validity, dict):
            raise ValueError("JANUS receipt is missing admission, handoff, or validity data")

        if receipt.get("decision") != "ALLOW":
            raise ValueError("JANUS receipt does not authorize admission")
        if str(receipt.get("authority", "")).strip().lower() != authority.strip().lower():
            raise ValueError("JANUS receipt authority does not match requested authority")
        if receipt.get("authorization_ref") != authorization_ref:
            raise ValueError("authorization_ref does not resolve to the supplied JANUS receipt")
        if handoff.get("authorization_ref") != authorization_ref:
            raise ValueError("JANUS handoff authorization_ref mismatch")
        if admission.get("state") != "AUTHORIZED" or admission.get("handoff_permitted") is not True:
            raise ValueError("JANUS receipt did not permit Packet OS handoff")
        if receipt.get("handoff_route") != "PACKET_OS" or handoff.get("destination") != "PACKET_OS":
            raise ValueError("JANUS receipt is not routed to Packet OS")
        if handoff.get("required") is not True or receipt.get("workforce_handoff_required") is not True:
            raise ValueError("JANUS receipt does not preserve required downstream handoff")

        expected = {
            "request_digest": packet.request_digest,
            "policy_snapshot_digest": packet.policy_snapshot_digest,
            "run_id": packet.run_id,
            "correlation_id": packet.correlation_id,
            "capability": packet.capability_request,
            "requested_by": packet.requested_by,
        }
        for field, expected_value in expected.items():
            if receipt.get(field) != expected_value:
                raise ValueError(f"JANUS receipt {field} does not match APF packet")
            if handoff.get(field) != expected_value:
                raise ValueError(f"JANUS handoff {field} does not match APF packet")

        expires_at = packet.authorization_expires_at
        if validity.get("expires_at") != expires_at or handoff.get("authorization_expires_at") != expires_at:
            raise ValueError("JANUS authorization expiry does not match APF packet")
        if validity.get("replay_after_expiry_permitted") is not False:
            raise ValueError("JANUS receipt must forbid replay after expiry")
        expiry = self._parse_utc(expires_at)
        if expiry <= datetime.now(timezone.utc):
            raise ValueError("JANUS authorization receipt is expired")

        supplied_digest = receipt.get("receipt_digest")
        if not isinstance(supplied_digest, str) or not supplied_digest.strip():
            raise ValueError("JANUS receipt_digest is required")
        digest_body = dict(receipt)
        digest_body.pop("receipt_digest", None)
        canonical = json.dumps(digest_body, sort_keys=True, separators=(",", ":")).encode()
        calculated_digest = hashlib.sha256(canonical).hexdigest()
        if not hmac.compare_digest(supplied_digest, calculated_digest):
            raise ValueError("JANUS receipt_digest mismatch")
        return supplied_digest

    @staticmethod
    def _parse_utc(value: str | None) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("authorization_expires_at is required")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("authorization_expires_at must be ISO-8601") from exc
        if parsed.tzinfo is None:
            raise ValueError("authorization_expires_at must include timezone")
        return parsed.astimezone(timezone.utc)

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
