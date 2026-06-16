from fastapi import APIRouter, Depends, Request

from app.models.requests import CreateSessionRequest
from app.models.responses import MessageResponse, SessionResponse
from app.repositories.session_repository import InMemorySessionRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_repo(request: Request) -> InMemorySessionRepository:
    return request.app.state.session_repo


@router.post("", response_model=SessionResponse)
def create_session(payload: CreateSessionRequest, repo: InMemorySessionRepository = Depends(get_session_repo)):
    session = repo.create_session(payload.tenant_id, payload.user_id, payload.title)
    return SessionResponse(
        session_id=session.session_id,
        tenant_id=session.tenant_id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages),
    )


@router.get("", response_model=list[SessionResponse])
def list_sessions(tenant_id: str, user_id: str, repo: InMemorySessionRepository = Depends(get_session_repo)):
    sessions = repo.list_sessions(tenant_id, user_id)
    return [
        SessionResponse(
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(session.messages),
        )
        for session in sessions
    ]


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: str, limit: int = 20, request: Request = None):
    repo: InMemorySessionRepository = request.app.state.session_repo
    messages = repo.get_recent_messages(session_id, limit)
    return [MessageResponse(role=m.role, content=m.content, created_at=m.created_at) for m in messages]
