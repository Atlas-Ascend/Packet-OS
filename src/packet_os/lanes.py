from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


class BackpressureError(RuntimeError):
    pass


@dataclass(slots=True)
class WorkLane:
    name: str
    concurrency: int
    queue_limit: int = 256
    weight: int = 1
    tags: frozenset[str] = field(default_factory=frozenset)
    paused: bool = False
    queue: deque[str] = field(default_factory=deque)
    in_flight: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("lane name is required")
        if self.concurrency < 1:
            raise ValueError("lane concurrency must be >= 1")
        if self.queue_limit < 1:
            raise ValueError("lane queue_limit must be >= 1")
        if self.weight < 1:
            raise ValueError("lane weight must be >= 1")

    @property
    def available_capacity(self) -> int:
        return 0 if self.paused else max(0, self.concurrency - len(self.in_flight))

    def offer(self, packet_id: str) -> None:
        if packet_id in self.in_flight or packet_id in self.queue:
            return
        if len(self.queue) >= self.queue_limit:
            raise BackpressureError(f"lane {self.name} queue is full")
        self.queue.append(packet_id)

    def claim(self) -> str | None:
        if self.available_capacity <= 0 or not self.queue:
            return None
        packet_id = self.queue.popleft()
        self.in_flight.add(packet_id)
        return packet_id

    def release(self, packet_id: str) -> None:
        self.in_flight.discard(packet_id)

    def metrics(self) -> dict[str, object]:
        return {
            "name": self.name,
            "queued": len(self.queue),
            "in_flight": len(self.in_flight),
            "concurrency": self.concurrency,
            "queue_limit": self.queue_limit,
            "weight": self.weight,
            "paused": self.paused,
            "available_capacity": self.available_capacity,
        }


class LaneScheduler:
    """Weighted fair scheduler with lane-local concurrency and backpressure."""

    def __init__(self, lanes: list[WorkLane]) -> None:
        if not lanes:
            raise ValueError("at least one work lane is required")
        self.lanes: dict[str, WorkLane] = {}
        for lane in lanes:
            if lane.name in self.lanes:
                raise ValueError(f"duplicate lane: {lane.name}")
            self.lanes[lane.name] = lane
        self._rotation = tuple(lane.name for lane in lanes for _ in range(lane.weight))
        self._cursor = 0
        self.packet_lane: dict[str, str] = {}

    def enqueue(self, packet_id: str, lane_name: str) -> None:
        try:
            lane = self.lanes[lane_name]
        except KeyError as exc:
            raise KeyError(f"unknown lane: {lane_name}") from exc
        lane.offer(packet_id)
        self.packet_lane[packet_id] = lane_name

    def claim_next(self) -> tuple[str, str] | None:
        if not self._rotation:
            return None
        for _ in range(len(self._rotation)):
            lane_name = self._rotation[self._cursor]
            self._cursor = (self._cursor + 1) % len(self._rotation)
            lane = self.lanes[lane_name]
            packet_id = lane.claim()
            if packet_id is not None:
                return lane_name, packet_id
        return None

    def release(self, packet_id: str) -> None:
        lane_name = self.packet_lane.get(packet_id)
        if lane_name:
            self.lanes[lane_name].release(packet_id)

    def pause(self, lane_name: str) -> None:
        self.lanes[lane_name].paused = True

    def resume(self, lane_name: str) -> None:
        self.lanes[lane_name].paused = False

    def metrics(self) -> dict[str, dict[str, object]]:
        return {name: lane.metrics() for name, lane in self.lanes.items()}


def standard_lanes() -> list[WorkLane]:
    return [
        WorkLane("research", concurrency=4, queue_limit=512, weight=2, tags=frozenset({"analysis", "discovery"})),
        WorkLane("build", concurrency=8, queue_limit=1024, weight=4, tags=frozenset({"implementation"})),
        WorkLane("integration", concurrency=4, queue_limit=512, weight=2, tags=frozenset({"wiring", "handoff"})),
        WorkLane("qa", concurrency=4, queue_limit=512, weight=3, tags=frozenset({"gaqc", "quality"})),
        WorkLane("deploy", concurrency=2, queue_limit=128, weight=1, tags=frozenset({"release"})),
        WorkLane("proof", concurrency=4, queue_limit=512, weight=2, tags=frozenset({"seca", "proofgrid"})),
        WorkLane("recovery", concurrency=2, queue_limit=256, weight=1, tags=frozenset({"devos", "repair"})),
    ]
