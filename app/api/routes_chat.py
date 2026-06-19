import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

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


@router.post("/stream")
def chat_stream(payload: ChatRequest, svc: RAGService = Depends(get_rag_service)):
    def event_stream():
        try:
            response = svc.answer(
                tenant_id=payload.tenant_id,
                user_id=payload.user_id,
                roles=payload.roles,
                query=payload.query,
                session_id=payload.session_id,
                top_k=payload.top_k,
            )
            yield _stream_event("session", session_id=response.session_id)
            for chunk in _chunk_text(response.answer):
                yield _stream_event("delta", text=chunk)
            yield _stream_event(
                "citations",
                citations=[citation.model_dump() for citation in response.citations],
            )
            yield _stream_event("done")
        except PermissionError as exc:
            yield _stream_event("error", detail=str(exc))
        except Exception as exc:
            yield _stream_event("error", detail=f"Chat request failed: {exc}")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _stream_event(event_type: str, **payload):
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"


def _chunk_text(text: str, chunk_size: int = 40):
    if not text:
        return
    for start in range(0, len(text), chunk_size):
        yield text[start : start + chunk_size]
