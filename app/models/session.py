from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ChatMessage:
    role: str  # user | assistant
    content: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ChatSession:
    session_id: str
    tenant_id: str
    user_id: str
    title: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: list[ChatMessage] = field(default_factory=list)
