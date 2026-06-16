from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    tenant_id: str
    text: str
    acl: list[str] = field(default_factory=list)
    chunk_index: int = 0
    pii_detected: bool = False
    secret_detected: bool = False
    guardrail_checked: bool = False
