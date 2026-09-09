from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .models import EvidenceRequirement


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class AtomicPacketSpec:
    key: str
    objective: str
    lane: str
    acceptance_criteria: tuple[str, ...]
    evidence_requirements: tuple[EvidenceRequirement, ...] = ()
    depends_on: tuple[str, ...] = ()
    priority: int = 50
    risk: RiskLevel = RiskLevel.MEDIUM
    constraints: tuple[str, ...] = ()
    idempotency_key: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.key.strip():
            raise ValueError("atomic packet key is required")
        if not self.objective.strip():
            raise ValueError(f"objective is required for {self.key}")
        if not self.lane.strip():
            raise ValueError(f"lane is required for {self.key}")
        if not self.acceptance_criteria:
            raise ValueError(f"acceptance criteria are required for {self.key}")
        if not 0 <= self.priority <= 100:
            raise ValueError(f"priority must be between 0 and 100 for {self.key}")
        if self.key in self.depends_on:
            raise ValueError(f"atomic packet cannot depend on itself: {self.key}")


class PacketGraph:
    """Dependency DAG for an atomic packet storm."""

    def __init__(self, specs: Iterable[AtomicPacketSpec]) -> None:
        self.specs: dict[str, AtomicPacketSpec] = {}
        for spec in specs:
            spec.validate()
            if spec.key in self.specs:
                raise ValueError(f"duplicate atomic packet key: {spec.key}")
            self.specs[spec.key] = spec

        unknown = {
            dependency
            for spec in self.specs.values()
            for dependency in spec.depends_on
            if dependency not in self.specs
        }
        if unknown:
            raise ValueError("unknown packet dependencies: " + ", ".join(sorted(unknown)))
        self._topological_order = self._build_topological_order()

    def _build_topological_order(self) -> tuple[str, ...]:
        incoming = {key: set(spec.depends_on) for key, spec in self.specs.items()}
        children: dict[str, set[str]] = {key: set() for key in self.specs}
        for key, deps in incoming.items():
            for dep in deps:
                children[dep].add(key)

        ready = sorted(key for key, deps in incoming.items() if not deps)
        order: list[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for child in sorted(children[current]):
                incoming[child].discard(current)
                if not incoming[child] and child not in order and child not in ready:
                    ready.append(child)
                    ready.sort()

        if len(order) != len(self.specs):
            cyclic = sorted(key for key, deps in incoming.items() if deps)
            raise ValueError("packet dependency cycle detected: " + ", ".join(cyclic))
        return tuple(order)

    def topological_order(self) -> tuple[str, ...]:
        return self._topological_order

    def waves(self) -> tuple[tuple[str, ...], ...]:
        remaining = set(self.specs)
        completed: set[str] = set()
        waves: list[tuple[str, ...]] = []
        while remaining:
            wave = tuple(
                sorted(
                    key
                    for key in remaining
                    if set(self.specs[key].depends_on).issubset(completed)
                )
            )
            if not wave:
                raise RuntimeError("graph became unschedulable")
            waves.append(wave)
            completed.update(wave)
            remaining.difference_update(wave)
        return tuple(waves)

    def ready(self, completed: set[str], admitted: set[str] | None = None) -> tuple[str, ...]:
        admitted = admitted or set()
        return tuple(
            key
            for key in self._topological_order
            if key not in completed
            and key not in admitted
            and set(self.specs[key].depends_on).issubset(completed)
        )

    def critical_path_length(self) -> int:
        distance: dict[str, int] = {}
        for key in self._topological_order:
            deps = self.specs[key].depends_on
            distance[key] = 1 + max((distance[dep] for dep in deps), default=0)
        return max(distance.values(), default=0)
