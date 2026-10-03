import unittest

from packet_os import PacketOS, PacketState, create_osiris_recovery_packet


class OSIRISRecoveryPacketTests(unittest.TestCase):
    def test_recovery_packet_closes_only_after_full_evidence_chain(self):
        os = PacketOS()
        packet = create_osiris_recovery_packet(
            os,
            checkpoint_id="estate-abc123",
            target="Atlas-Ascend/Ghost-Atlas-Command-Center",
            reason="bounded recovery drill",
        )

        self.assertEqual(packet.metadata["capability_id"], "estate.recovery.route")
        self.assertEqual(packet.inputs["checkpoint_id"], "estate-abc123")
        self.assertEqual(
            {item.kind for item in packet.evidence_requirements},
            {"checkpoint", "execution", "seca-verification", "proofgrid", "thoth-post-checkpoint"},
        )

        os.authorize(packet.packet_id, authority="JANUS-PRIME", authorization_ref="janus:recovery:001")
        os.transition(packet.packet_id, PacketState.QUEUED, actor="JANUS-PRIME")
        os.claim(packet.packet_id, worker="PROMETHEUS")
        os.transition(packet.packet_id, PacketState.RUNNING, actor="PROMETHEUS")

        for kind, producer in [
            ("checkpoint", "THOTH"),
            ("execution", "EXECUTION-FABRIC"),
            ("seca-verification", "SECA"),
            ("proofgrid", "PROOFGRID"),
            ("thoth-post-checkpoint", "THOTH"),
        ]:
            os.attach_evidence(
                packet.packet_id,
                kind=kind,
                uri=f"proof://osiris/{kind}",
                producer=producer,
                payload={"status": "PASS", "kind": kind},
            )

        os.transition(packet.packet_id, PacketState.REVIEW, actor="PROMETHEUS")
        os.verify_packet(packet.packet_id, actor="SECA")
        os.complete_packet(packet.packet_id, actor="SECA")

        self.assertEqual(packet.state, PacketState.COMPLETED)
        self.assertEqual(packet.metadata["recovery_role"], "OSIRIS-RECOVERY")

    def test_recovery_packet_rejects_missing_checkpoint(self):
        with self.assertRaises(ValueError):
            create_osiris_recovery_packet(
                PacketOS(),
                checkpoint_id="",
                target="EDEN",
                reason="test",
            )


if __name__ == "__main__":
    unittest.main()
