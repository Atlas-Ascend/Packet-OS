from __future__ import annotations

import argparse
import json

from .models import EvidenceRequirement, PacketState
from .service import PacketOS


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


def main() -> None:
    parser = argparse.ArgumentParser(prog="packet-os")
    parser.add_argument("command", choices=["demo"], nargs="?", default="demo")
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
