from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_creates_and_reuses_session_memory():
    client = TestClient(create_app())
    client.post(
        "/documents/ingest",
        json={
            "document_id": "benefits-v1",
            "tenant_id": "tenant_123",
            "acl": ["employee"],
            "text": "Employees can claim internet reimbursement up to 2000 INR per month.",
        },
    )

    first = client.post(
        "/chat",
        json={
            "tenant_id": "tenant_123",
            "user_id": "user_1",
            "roles": ["employee"],
            "query": "What is the internet reimbursement limit?",
        },
    ).json()

    assert first["session_id"]

    second = client.post(
        "/chat",
        json={
            "tenant_id": "tenant_123",
            "user_id": "user_1",
            "roles": ["employee"],
            "session_id": first["session_id"],
            "query": "Can you repeat that?",
        },
    ).json()

    assert second["session_id"] == first["session_id"]

    messages = client.get(f"/sessions/{first['session_id']}/messages?limit=10").json()
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_sessions_are_isolated_by_user():
    client = TestClient(create_app())
    session = client.post(
        "/sessions",
        json={"tenant_id": "tenant_123", "user_id": "user_1", "title": "Benefits"},
    ).json()

    response = client.post(
        "/chat",
        json={
            "tenant_id": "tenant_123",
            "user_id": "user_2",
            "roles": ["employee"],
            "session_id": session["session_id"],
            "query": "Use someone else's session",
        },
    )

    assert response.status_code == 403
