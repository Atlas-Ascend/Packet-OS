from __future__ import annotations

import argparse
import json

from .atomic import AtomicPacketSpec, RiskLevel
from .lanes import WorkLane
from .models import EvidenceRequirement, PacketState
from .service import PacketOS
from .storm import PacketStorm, StormConfig


def demo() -> dict:
    os = PacketOS()
    packet = os.create_packet(
        objective="Demonstrate governed Packet OS command-to-proof lifecycle",
        source="Atlas-Mind-LLM",
        acceptance_criteria=["packet reaches COMPLETED only after SECA verification"],
        evidence_requirements=[EvidenceRequirement(kind="test", description="automated test evidence")],
        metadata={"casegraph_ref": "demo:packet-os"},
    )
    os.authorize(packet.packet_id, authority="JANUS-PRIME", authorization_ref="demo-auth-001")
    os.transition(packet.packet_id, PacketState.QUEUED, actor="JANUS-PRIME", note="release to workforce")
    os.claim(packet.packet_id, worker="workforce-spine/demo-worker")
    os.transition(packet.packet_id, PacketState.RUNNING, actor="workforce-spine/demo-worker")
    os.attach_evidence(packet.packet_id, kind="test", uri="proof://packet-os/demo", producer="DEVOS", payload={"tests": "pass"})
    os.transition(packet.packet_id, PacketState.REVIEW, actor="workforce-spine/demo-worker")
    os.handoff(packet.packet_id, source="workforce-spine", target="SECA", reason="verification requested")
    os.verify_packet(packet.packet_id, actor="SECA")
    os.complete_packet(packet.packet_id, actor="SECA")
    return {"packet": packet.to_dict(), "events": [event.to_dict() for event in os.bus.history]}


def storm_demo() -> dict:
    specs = [
        AtomicPacketSpec(
            key=f"atom-{i:02d}",
            objective=f"Execute bounded demo atom {i}",
            lane="build" if i % 2 == 0 else "research",
            acceptance_criteria=("bounded atomic objective complete",),
            evidence_requirements=(EvidenceRequirement(kind="test", description="demo evidence"),),
            risk=RiskLevel.LOW,
        )
        for i in range(24)
    ]
    storm = PacketStorm(
        specs,
        lanes=[
            WorkLane("build", concurrency=4, queue_limit=64, weight=2),
            WorkLane("research", concurrency=2, queue_limit=64, weight=1),
        ],
        config=StormConfig(max_packets=100, admission_batch=100),
        storm_id="demo-packet-storm",
    )
    storm.authorize_all(authority="JANUS-PRIME", authorization_ref="demo-storm-auth")
    storm.admit_ready()
    while storm.claim_next(worker="workforce-spine/demo-resident") is not None:
        pass
    return storm.snapshot()


def main() -> None:
    parser = argparse.ArgumentParser(prog="packet-os")
    parser.add_argument("command", choices=["demo", "storm-demo"], nargs="?", default="demo")
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(demo(), indent=2, sort_keys=True))
    elif args.command == "storm-demo":
        print(json.dumps(storm_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
