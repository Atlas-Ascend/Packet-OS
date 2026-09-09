from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from .models import PacketEvent

Handler = Callable[[PacketEvent], None]


class EventBus:
    """Small in-process adapter; production transports bind the same event contract."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self.history: list[PacketEvent] = []

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: PacketEvent) -> None:
        self.history.append(event)
        for handler in self._handlers.get(event.event_type, []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)
