from app.repositories.audit_repository import AuditEvent, InMemoryAuditRepository


class AuditService:
    def __init__(self, repo: InMemoryAuditRepository):
        self.repo = repo

    def record(self, event_type: str, document_id: str | None = None, chunk_id: str | None = None, **details):
        self.repo.add(AuditEvent(event_type=event_type, document_id=document_id, chunk_id=chunk_id, details=details))
