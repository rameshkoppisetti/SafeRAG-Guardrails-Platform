from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    document_id: str = Field(..., examples=["refund-policy-v1"])
    tenant_id: str = Field(..., examples=["tenant_123"])
    text: str
    acl: list[str] = Field(default_factory=list, examples=[["support", "admin"]])


class ChatRequest(BaseModel):
    tenant_id: str
    user_id: str
    roles: list[str] = Field(default_factory=list)
    query: str
    session_id: str | None = None
    top_k: int | None = None


class CreateSessionRequest(BaseModel):
    tenant_id: str
    user_id: str
    title: str | None = None
