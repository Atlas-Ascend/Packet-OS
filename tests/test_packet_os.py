import unittest

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


if __name__ == "__main__":
    unittest.main()
