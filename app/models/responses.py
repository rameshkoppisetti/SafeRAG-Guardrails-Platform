from pydantic import BaseModel


class IngestDocumentResponse(BaseModel):
    document_id: str
    accepted_chunks: int
    blocked_chunks: int


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[Citation]


class SessionResponse(BaseModel):
    session_id: str
    tenant_id: str
    user_id: str
    title: str | None = None
    created_at: str
    updated_at: str
    message_count: int


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: str
