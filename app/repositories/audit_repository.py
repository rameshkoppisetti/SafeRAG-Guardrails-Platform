from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    document_id: str | None = None
    chunk_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InMemoryAuditRepository:
    def __init__(self):
        self._events: list[AuditEvent] = []

    def add(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)
