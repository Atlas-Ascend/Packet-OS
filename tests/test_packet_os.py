import hashlib
import json
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from packet_os import EvidenceRequirement, PacketOS, PacketState


class PacketOSTests(unittest.TestCase):
    def make_packet(self, required_kind: str = "test"):
        os = PacketOS()
        packet = os.create_packet(
            objective="Ship bounded work",
            source="Atlas-Mind-LLM",
            acceptance_criteria=["verified output exists"],
            evidence_requirements=[EvidenceRequirement(kind=required_kind, description="proof")],
        )
        os.authorize(packet.packet_id, authority="JANUS-PRIME", authorization_ref="auth:1")
        return os, packet

    def make_apf_packet(self, *, expires_at: str | None = None):
        os = PacketOS()
        issued = datetime.now(timezone.utc)
        expires_at = expires_at or (issued + timedelta(minutes=5)).isoformat()
        packet = os.create_packet(
            packet_id="apf-packet-001",
            correlation_id="corr-001",
            run_id="run-001",
            attempt=1,
            requested_by="architect:ghost-atlas",
            capability_request="estate.reconcile",
            request_digest="a" * 64,
            policy_snapshot_digest="b" * 64,
            authorization_expires_at=expires_at,
            objective="Execute governed APF work",
            source="JANUS-ATLAS-PROMPT-FABRIC",
            acceptance_criteria=["authorization lineage preserved"],
            evidence_requirements=[EvidenceRequirement(kind="test", description="proof")],
        )
        receipt = {
            "decision_id": "auth-apf-001",
            "authorization_ref": "auth-apf-001",
            "decision": "ALLOW",
            "authority": "janus-prime",
            "policy_id": "janus-runtime-gate-v1",
            "policy_snapshot_digest": packet.policy_snapshot_digest,
            "request_digest": packet.request_digest,
            "run_id": packet.run_id,
            "correlation_id": packet.correlation_id,
            "capability": packet.capability_request,
            "requested_by": packet.requested_by,
            "admission": {
                "state": "AUTHORIZED",
                "handoff_permitted": True,
                "exception_required": False,
            },
            "validity": {
                "issued_at": issued.isoformat(),
                "expires_at": expires_at,
                "ttl_seconds": 300,
                "replay_after_expiry_permitted": False,
            },
            "handoff_route": "PACKET_OS",
            "handoff": {
                "required": True,
                "destination": "PACKET_OS",
                "authorization_ref": "auth-apf-001",
                "request_digest": packet.request_digest,
                "policy_snapshot_digest": packet.policy_snapshot_digest,
                "authorization_expires_at": expires_at,
                "run_id": packet.run_id,
                "correlation_id": packet.correlation_id,
                "capability": packet.capability_request,
                "requested_by": packet.requested_by,
            },
            "workforce_handoff_required": True,
            "reasons": ["AUTHENTICATED_ARCHITECT_INGRESS", "CAPABILITY_ALLOWED"],
            "decided_at": issued.isoformat(),
        }
        self.resign_receipt(receipt)
        return os, packet, receipt

    @staticmethod
    def resign_receipt(receipt):
        body = dict(receipt)
        body.pop("receipt_digest", None)
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        receipt["receipt_digest"] = hashlib.sha256(canonical).hexdigest()

    def drive_to_review(self, os, packet):
        os.transition(packet.packet_id, PacketState.QUEUED, actor="JANUS-PRIME")
        os.claim(packet.packet_id, worker="worker-1")
        os.transition(packet.packet_id, PacketState.RUNNING, actor="worker-1")
        os.transition(packet.packet_id, PacketState.REVIEW, actor="worker-1")

    def test_happy_path_requires_verification_before_completion(self):
        os, packet = self.make_packet()
        os.transition(packet.packet_id, PacketState.QUEUED, actor="JANUS-PRIME")
        os.claim(packet.packet_id, worker="worker-1")
        os.transition(packet.packet_id, PacketState.RUNNING, actor="worker-1")
        os.attach_evidence(packet.packet_id, kind="test", uri="proof://1", producer="DEVOS", payload={"ok": True})
        os.transition(packet.packet_id, PacketState.REVIEW, actor="worker-1")
        os.verify_packet(packet.packet_id, actor="SECA")
        os.complete_packet(packet.packet_id, actor="SECA")
        self.assertEqual(packet.state, PacketState.COMPLETED)

    def test_illegal_transition_rejected(self):
        os, packet = self.make_packet()
        with self.assertRaises(ValueError):
            os.transition(packet.packet_id, PacketState.RUNNING, actor="worker-1")

    def test_non_seca_verification_rejected(self):
        os, packet = self.make_packet()
        self.drive_to_review(os, packet)
        os.attach_evidence(packet.packet_id, kind="test", uri="proof://1", producer="DEVOS", payload={"ok": True})
        with self.assertRaises(PermissionError):
            os.verify_packet(packet.packet_id, actor="JANUS-PRIME")

    def test_missing_required_evidence_blocks_verification(self):
        os, packet = self.make_packet("security-scan")
        self.drive_to_review(os, packet)
        with self.assertRaises(ValueError):
            os.verify_packet(packet.packet_id, actor="SECA")

    def test_event_bus_records_lifecycle(self):
        os, packet = self.make_packet()
        self.assertGreaterEqual(len(os.bus.history), 2)
        self.assertEqual(os.bus.history[0].event_type, "packet.created")
        self.assertEqual(os.bus.history[1].event_type, "packet.state.changed")

    def test_apf_authorization_accepts_exact_janus_receipt_and_preserves_identity(self):
        os, packet, receipt = self.make_apf_packet()
        os.authorize(
            packet.packet_id,
            authority="janus-prime",
            authorization_ref="auth-apf-001",
            authorization_receipt=receipt,
        )
        self.assertEqual(packet.state, PacketState.AUTHORIZED)
        self.assertEqual(packet.packet_id, "apf-packet-001")
        self.assertEqual(packet.run_id, "run-001")
        self.assertEqual(packet.correlation_id, "corr-001")
        self.assertEqual(packet.metadata["authorization_proof"], "JANUS_RECEIPT_VERIFIED")
        self.assertEqual(packet.metadata["authorization_receipt_digest"], receipt["receipt_digest"])

    def test_apf_authorization_rejects_missing_receipt(self):
        os, packet, _ = self.make_apf_packet()
        with self.assertRaisesRegex(ValueError, "exact JANUS authorization receipt"):
            os.authorize(packet.packet_id, authority="janus-prime", authorization_ref="auth-apf-001")

    def test_apf_authorization_rejects_unresolved_authorization_ref(self):
        os, packet, receipt = self.make_apf_packet()
        with self.assertRaisesRegex(ValueError, "authorization_ref"):
            os.authorize(
                packet.packet_id,
                authority="janus-prime",
                authorization_ref="auth-missing",
                authorization_receipt=receipt,
            )

    def test_apf_authorization_rejects_request_digest_mismatch(self):
        os, packet, receipt = self.make_apf_packet()
        receipt = deepcopy(receipt)
        receipt["request_digest"] = "c" * 64
        receipt["handoff"]["request_digest"] = "c" * 64
        self.resign_receipt(receipt)
        with self.assertRaisesRegex(ValueError, "request_digest"):
            os.authorize(
                packet.packet_id,
                authority="janus-prime",
                authorization_ref="auth-apf-001",
                authorization_receipt=receipt,
            )

    def test_apf_authorization_rejects_policy_digest_mismatch(self):
        os, packet, receipt = self.make_apf_packet()
        receipt = deepcopy(receipt)
        receipt["policy_snapshot_digest"] = "d" * 64
        receipt["handoff"]["policy_snapshot_digest"] = "d" * 64
        self.resign_receipt(receipt)
        with self.assertRaisesRegex(ValueError, "policy_snapshot_digest"):
            os.authorize(
                packet.packet_id,
                authority="janus-prime",
                authorization_ref="auth-apf-001",
                authorization_receipt=receipt,
            )

    def test_apf_authorization_rejects_requester_principal_mismatch(self):
        os, packet, receipt = self.make_apf_packet()
        receipt = deepcopy(receipt)
        receipt["requested_by"] = "architect:other"
        receipt["handoff"]["requested_by"] = "architect:other"
        self.resign_receipt(receipt)
        with self.assertRaisesRegex(ValueError, "requested_by"):
            os.authorize(
                packet.packet_id,
                authority="janus-prime",
                authorization_ref="auth-apf-001",
                authorization_receipt=receipt,
            )

    def test_apf_authorization_rejects_expired_receipt(self):
        expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        os, packet, receipt = self.make_apf_packet(expires_at=expired)
        with self.assertRaisesRegex(ValueError, "expired"):
            os.authorize(
                packet.packet_id,
                authority="janus-prime",
                authorization_ref="auth-apf-001",
                authorization_receipt=receipt,
            )

    def test_apf_authorization_rejects_tampered_receipt_digest(self):
        os, packet, receipt = self.make_apf_packet()
        receipt = deepcopy(receipt)
        receipt["receipt_digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "receipt_digest mismatch"):
            os.authorize(
                packet.packet_id,
                authority="janus-prime",
                authorization_ref="auth-apf-001",
                authorization_receipt=receipt,
            )


if __name__ == "__main__":
    unittest.main()
