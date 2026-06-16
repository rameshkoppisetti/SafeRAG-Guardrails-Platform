from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from uuid import UUID, uuid4


from app.models.session import ChatMessage, ChatSession


class InMemorySessionRepository:
    """Dev/test repository. Use PostgresSessionRepository in production."""

    def __init__(self):
        self._lock = RLock()
        self._sessions: dict[str, ChatSession] = {}

    def create_session(self, tenant_id: str, user_id: str, title: str | None = None) -> ChatSession:
        with self._lock:
            session = ChatSession(session_id=str(uuid4()), tenant_id=tenant_id, user_id=user_id, title=title)
            self._sessions[session.session_id] = session
            return session

    def get_or_create_session(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str | None,
        title: str | None = None,
    ) -> ChatSession:
        with self._lock:
            if session_id:
                session = self._sessions.get(session_id)
                if session:
                    if session.tenant_id != tenant_id or session.user_id != user_id:
                        raise PermissionError("Session does not belong to this tenant/user")
                    return session
                raise PermissionError("Session not found for this tenant/user")
            return self.create_session(tenant_id=tenant_id, user_id=user_id, title=title)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.messages.append(ChatMessage(role=role, content=content))
            session.updated_at = datetime.now(timezone.utc).isoformat()

    def get_recent_messages(self, session_id: str, limit: int = 8) -> list[ChatMessage]:
        with self._lock:
            session = self._sessions[session_id]
            return list(session.messages[-limit:])

    def list_sessions(self, tenant_id: str, user_id: str) -> list[ChatSession]:
        with self._lock:
            return [s for s in self._sessions.values() if s.tenant_id == tenant_id and s.user_id == user_id]


class PostgresSessionRepository:
    """Persistent session memory backed by Postgres."""

    def __init__(self, connection_string: str, min_size: int = 1, max_size: int = 5):
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        self.pool = ConnectionPool(
            conninfo=connection_string,
            min_size=min_size,
            max_size=max_size,
            kwargs={"row_factory": dict_row},
            open=True,
        )
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id UUID PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            title TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant_user_updated
        ON chat_sessions (tenant_id, user_id, updated_at DESC);
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id BIGSERIAL PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
        ON chat_messages (session_id, created_at ASC, message_id ASC);
        """
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema)
            conn.commit()

    def create_session(self, tenant_id: str, user_id: str, title: str | None = None) -> ChatSession:
        session_id = str(uuid4())
        with self.pool.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO chat_sessions (session_id, tenant_id, user_id, title)
                VALUES (%s, %s, %s, %s)
                RETURNING session_id, tenant_id, user_id, title, created_at, updated_at
                """,
                (session_id, tenant_id, user_id, title),
            ).fetchone()
            conn.commit()
        return self._row_to_session(row, [])

    def get_or_create_session(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str | None,
        title: str | None = None,
    ) -> ChatSession:
        if not session_id:
            return self.create_session(tenant_id, user_id, title)

        try:
            UUID(session_id)
        except ValueError as exc:
            raise PermissionError("Invalid session_id") from exc

        with self.pool.connection() as conn:
            row = conn.execute(
                """
                SELECT session_id, tenant_id, user_id, title, created_at, updated_at
                FROM chat_sessions
                WHERE session_id = %s
                """,
                (session_id,),
            ).fetchone()

        if not row:
            raise PermissionError("Session not found for this tenant/user")
        if row["tenant_id"] != tenant_id or row["user_id"] != user_id:
            raise PermissionError("Session does not belong to this tenant/user")
        return self._row_to_session(row, [])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (session_id, role, content)
                VALUES (%s, %s, %s)
                """,
                (session_id, role, content),
            )
            conn.execute(
                "UPDATE chat_sessions SET updated_at = NOW() WHERE session_id = %s",
                (session_id,),
            )
            conn.commit()

    def get_recent_messages(self, session_id: str, limit: int = 8) -> list[ChatMessage]:
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at DESC, message_id DESC
                LIMIT %s
                """,
                (session_id, limit),
            ).fetchall()
        return [self._row_to_message(row) for row in reversed(rows)]

    def list_sessions(self, tenant_id: str, user_id: str) -> list[ChatSession]:
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    s.session_id,
                    s.tenant_id,
                    s.user_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    COUNT(m.message_id) AS message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON m.session_id = s.session_id
                WHERE s.tenant_id = %s AND s.user_id = %s
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
                """,
                (tenant_id, user_id),
            ).fetchall()
        sessions = []
        for row in rows:
            session = self._row_to_session(row, [])
            # keep message_count available for API without loading full messages
            session.messages = [ChatMessage(role="system", content="__count_placeholder__")] * int(row.get("message_count", 0))
            sessions.append(session)
        return sessions

    def _row_to_session(self, row: dict, messages: list[ChatMessage]) -> ChatSession:
        return ChatSession(
            session_id=str(row["session_id"]),
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            title=row.get("title"),
            created_at=row["created_at"].isoformat(),
            updated_at=row["updated_at"].isoformat(),
            messages=messages,
        )

    def _row_to_message(self, row: dict) -> ChatMessage:
        return ChatMessage(
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"].isoformat(),
        )


class SessionRepositoryFactory:
    @staticmethod
    def create(backend: str, postgres_connection: str):
        backend = backend.lower()
        if backend == "memory":
            return InMemorySessionRepository()
        if backend == "postgres":
            return PostgresSessionRepository(postgres_connection)
        raise ValueError(f"Unsupported SESSION_BACKEND={backend}. Use memory or postgres.")
