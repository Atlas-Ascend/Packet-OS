import unittest

from packet_os.models import PacketState
from packet_os.state_machine import APF_TO_PACKET_STATES, packet_states_for_apf_state


class APFLifecycleMappingTests(unittest.TestCase):
    def test_apf_semantics_project_onto_existing_packet_states(self):
        expected = {
            "ADMITTED": (PacketState.DRAFT,),
            "AUTHORIZED": (PacketState.AUTHORIZED,),
            "READY": (PacketState.QUEUED,),
            "DISPATCHED": (PacketState.QUEUED,),
            "ACKNOWLEDGED": (PacketState.CLAIMED,),
            "RUNNING": (PacketState.RUNNING,),
            "VERIFYING": (PacketState.REVIEW, PacketState.VERIFIED),
            "COMPLETED": (PacketState.COMPLETED,),
            "FAILED": (PacketState.FAILED,),
            "BLOCKED": (PacketState.BLOCKED,),
            "ROLLED_BACK": (PacketState.CANCELLED,),
        }
        self.assertEqual(APF_TO_PACKET_STATES, expected)

    def test_mapping_is_case_insensitive_and_rejects_unknown_semantics(self):
        self.assertEqual(packet_states_for_apf_state("ready"), (PacketState.QUEUED,))
        with self.assertRaisesRegex(ValueError, "unknown APF lifecycle state"):
            packet_states_for_apf_state("PROMOTED")

    def test_apf_terms_do_not_create_parallel_packet_states(self):
        for semantic in APF_TO_PACKET_STATES:
            if semantic in PacketState.__members__:
                self.assertIn(semantic, {"AUTHORIZED", "RUNNING", "COMPLETED", "FAILED", "BLOCKED"})


if __name__ == "__main__":
    unittest.main()
