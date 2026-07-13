"""Best-effort business event recording."""

from typing import List

from .models import DomainEvent
from .repositories import EventRepository


class AnalyticsService:
    """Analytics is deliberately non-blocking for core transactions."""

    def __init__(self, events: EventRepository):
        self.events = events
        self.failed_events: List[DomainEvent] = []

    def record(self, event: DomainEvent) -> None:
        try:
            self.events.save(event)
        except Exception:
            self.failed_events.append(event)

    def list_events(self, name=None) -> List[DomainEvent]:
        if name is None:
            return list(self.events.items)
        return [event for event in self.events.items if event.name == name]

