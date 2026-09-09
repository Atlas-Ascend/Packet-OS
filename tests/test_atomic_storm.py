import unittest

from packet_os import EvidenceRequirement, PacketState
from packet_os.atomic import AtomicPacketSpec, PacketGraph, RiskLevel
from packet_os.gaqc import GAQCDisposition, QualityDefect
from packet_os.lanes import BackpressureError, LaneScheduler, WorkLane
from packet_os.storm import PacketStorm, StormConfig


def spec(
    key: str,
    *,
    lane: str = "build",
    deps: tuple[str, ...] = (),
    risk: RiskLevel = RiskLevel.HIGH,
) -> AtomicPacketSpec:
    return AtomicPacketSpec(
        key=key,
        objective=f"execute {key}",
        lane=lane,
        acceptance_criteria=(f"{key} complete",),
        evidence_requirements=(EvidenceRequirement("test", "automated test receipt"),),
        depends_on=deps,
        risk=risk,
    )


class AtomicGraphTests(unittest.TestCase):
    def test_graph_builds_parallel_waves_and_critical_path(self):
        graph = PacketGraph([
            spec("research", lane="research"),
            spec("api"),
            spec("ui"),
            spec("integrate", lane="integration", deps=("api", "ui")),
            spec("proof", lane="proof", deps=("research", "integrate")),
        ])
        self.assertEqual(graph.waves()[0], ("api", "research", "ui"))
        self.assertEqual(graph.waves()[-1], ("proof",))
        self.assertEqual(graph.critical_path_length(), 3)

    def test_cycle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            PacketGraph([spec("a", deps=("b",)), spec("b", deps=("a",))])

    def test_unknown_dependency_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown packet dependencies"):
            PacketGraph([spec("a", deps=("missing",))])


class LaneSchedulerTests(unittest.TestCase):
    def test_lane_concurrency_and_backpressure_are_enforced(self):
        lane = WorkLane("build", concurrency=2, queue_limit=2)
        scheduler = LaneScheduler([lane])
        scheduler.enqueue("p1", "build")
        scheduler.enqueue("p2", "build")
        with self.assertRaises(BackpressureError):
            scheduler.enqueue("p3", "build")
        self.assertIsNotNone(scheduler.claim_next())
        self.assertIsNotNone(scheduler.claim_next())
        self.assertIsNone(scheduler.claim_next())
        scheduler.release("p1")
        scheduler.enqueue("p3", "build")
        self.assertIsNotNone(scheduler.claim_next())

    def test_weighted_rotation_services_multiple_lanes(self):
        scheduler = LaneScheduler([
            WorkLane("research", concurrency=4, weight=1),
            WorkLane("build", concurrency=4, weight=3),
        ])
        for i in range(4):
            scheduler.enqueue(f"r{i}", "research")
            scheduler.enqueue(f"b{i}", "build")
        claims = [scheduler.claim_next()[0] for _ in range(4)]
        self.assertEqual(claims.count("build"), 3)
        self.assertEqual(claims.count("research"), 1)


class GAQCTests(unittest.TestCase):
    def test_high_risk_packet_is_always_inspected_and_passes_only_to_seca(self):
        storm = PacketStorm([spec("a")], lanes=[WorkLane("build", 1)])
        storm.authorize_all(authority="JANUS", authorization_ref="auth")
        storm.admit_ready()
        packet = storm.claim_next(worker="worker")
        storm.start(packet.packet_id, actor="worker")
        storm.packet_os.attach_evidence(
            packet.packet_id,
            kind="test",
            uri="proof://test",
            producer="worker",
            payload={"passed": True},
        )
        storm.submit_for_review(packet.packet_id, actor="worker")
        decision = storm.inspect_quality(packet.packet_id)
        self.assertEqual(decision.disposition, GAQCDisposition.PASS_TO_SECA)
        self.assertEqual(storm.packet_os.packets[packet.packet_id].state, PacketState.REVIEW)
        with self.assertRaises(PermissionError):
            storm.seca_verify(packet.packet_id, actor="GAQC")

    def test_missing_evidence_routes_rework(self):
        storm = PacketStorm([spec("a")], lanes=[WorkLane("build", 1)])
        storm.authorize_all(authority="JANUS", authorization_ref="auth")
        storm.admit_ready()
        packet = storm.claim_next(worker="worker")
        storm.start(packet.packet_id, actor="worker")
        storm.submit_for_review(packet.packet_id, actor="worker")
        decision = storm.inspect_quality(packet.packet_id)
        self.assertEqual(decision.disposition, GAQCDisposition.REWORK)
        self.assertEqual(decision.missing_evidence, ("test",))
        targets = [event.target for event in storm.packet_os.bus.history if event.event_type == "packet.handoff"]
        self.assertIn("DEVOS", targets)

    def test_critical_defect_escalates_to_janus(self):
        storm = PacketStorm([spec("a")], lanes=[WorkLane("build", 1)])
        storm.authorize_all(authority="JANUS", authorization_ref="auth")
        storm.admit_ready()
        packet = storm.claim_next(worker="worker")
        storm.start(packet.packet_id, actor="worker")
        storm.submit_for_review(packet.packet_id, actor="worker")
        decision = storm.inspect_quality(
            packet.packet_id,
            defects=(QualityDefect("SECURITY_BOUNDARY", RiskLevel.CRITICAL),),
        )
        self.assertEqual(decision.disposition, GAQCDisposition.ESCALATE)


class PacketStormTests(unittest.TestCase):
    def test_dependencies_release_next_wave_only_after_completion(self):
        storm = PacketStorm(
            [spec("a"), spec("b", deps=("a",)), spec("c", deps=("a",))],
            lanes=[WorkLane("build", 4)],
        )
        storm.authorize_all(authority="JANUS", authorization_ref="auth")
        self.assertEqual(storm.admit_ready(), ("a",))

        packet = storm.claim_next(worker="worker")
        storm.start(packet.packet_id, actor="worker")
        storm.packet_os.attach_evidence(
            packet.packet_id,
            kind="test",
            uri="proof://a",
            producer="worker",
            payload={"passed": True},
        )
        storm.submit_for_review(packet.packet_id, actor="worker")
        storm.inspect_quality(packet.packet_id)
        storm.seca_verify(packet.packet_id)
        storm.complete(packet.packet_id, actor="JANUS")

        states = {key: storm.packet_os.packets[packet_id].state for key, packet_id in storm.packet_by_key.items()}
        self.assertEqual(states["a"], PacketState.COMPLETED)
        self.assertEqual(states["b"], PacketState.QUEUED)
        self.assertEqual(states["c"], PacketState.QUEUED)

    def test_hundred_packet_storm_respects_lane_capacity(self):
        specs = [
            spec(
                f"packet-{i:03d}",
                lane=("build" if i % 2 == 0 else "research"),
                risk=RiskLevel.LOW,
            )
            for i in range(100)
        ]
        storm = PacketStorm(
            specs,
            lanes=[
                WorkLane("build", concurrency=8, queue_limit=100),
                WorkLane("research", concurrency=4, queue_limit=100),
            ],
            config=StormConfig(max_packets=1000, admission_batch=1000),
        )
        storm.authorize_all(authority="JANUS", authorization_ref="storm-auth")
        admitted = storm.admit_ready()
        self.assertEqual(len(admitted), 100)

        claimed = []
        while True:
            packet = storm.claim_next(worker="resident-workforce")
            if packet is None:
                break
            claimed.append(packet)

        self.assertEqual(len(claimed), 12)
        metrics = storm.scheduler.metrics()
        self.assertEqual(metrics["build"]["in_flight"], 8)
        self.assertEqual(metrics["research"]["in_flight"], 4)
        self.assertEqual(metrics["build"]["queued"], 42)
        self.assertEqual(metrics["research"]["queued"], 46)

    def test_storm_size_guard_rejects_unbounded_fanout(self):
        with self.assertRaisesRegex(ValueError, "max_packets"):
            PacketStorm(
                [spec("a"), spec("b")],
                lanes=[WorkLane("build", 1)],
                config=StormConfig(max_packets=1),
            )


if __name__ == "__main__":
    unittest.main()
