from __future__ import annotations

from .models import PacketState


# Atlas Prompt Fabric lifecycle terms are an interface projection over Packet OS.
# PacketState remains the only executable state machine.
APF_TO_PACKET_STATES: dict[str, tuple[PacketState, ...]] = {
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


def packet_states_for_apf_state(apf_state: str) -> tuple[PacketState, ...]:
    normalized = apf_state.strip().upper()
    try:
        return APF_TO_PACKET_STATES[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown APF lifecycle state: {apf_state}") from exc


ALLOWED_TRANSITIONS: dict[PacketState, set[PacketState]] = {
    PacketState.DRAFT: {PacketState.AUTHORIZED, PacketState.CANCELLED},
    PacketState.AUTHORIZED: {PacketState.QUEUED, PacketState.CANCELLED},
    PacketState.QUEUED: {PacketState.CLAIMED, PacketState.BLOCKED, PacketState.CANCELLED},
    PacketState.CLAIMED: {PacketState.RUNNING, PacketState.BLOCKED, PacketState.CANCELLED},
    PacketState.RUNNING: {PacketState.REVIEW, PacketState.BLOCKED, PacketState.FAILED},
    PacketState.BLOCKED: {PacketState.QUEUED, PacketState.CLAIMED, PacketState.FAILED, PacketState.CANCELLED},
    PacketState.REVIEW: {PacketState.VERIFIED, PacketState.RUNNING, PacketState.FAILED},
    PacketState.VERIFIED: {PacketState.COMPLETED, PacketState.RUNNING},
    PacketState.FAILED: {PacketState.QUEUED, PacketState.CANCELLED},
    PacketState.COMPLETED: set(),
    PacketState.CANCELLED: set(),
}


def assert_transition(current: PacketState, target: PacketState) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"illegal packet transition: {current.value} -> {target.value}")
