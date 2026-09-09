from __future__ import annotations

from .models import PacketState


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
