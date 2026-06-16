from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_rag_service(request: Request):
    return request.app.state.rag_service


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, svc: RAGService = Depends(get_rag_service)):
    try:
        return svc.answer(
            tenant_id=payload.tenant_id,
            user_id=payload.user_id,
            roles=payload.roles,
            query=payload.query,
            session_id=payload.session_id,
            top_k=payload.top_k,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
