import json

from fastapi.testclient import TestClient

from app.main import create_app


def test_ingest_and_chat_flow():
    client = TestClient(create_app())

    ingest_resp = client.post(
        "/documents/ingest",
        json={
            "document_id": "refund-policy-v1",
            "tenant_id": "tenant_123",
            "acl": ["support"],
            "text": "Refunds are processed within 7 business days. Contact support for refund status.",
        },
    )
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["accepted_chunks"] == 1

    chat_resp = client.post(
        "/chat",
        json={
            "tenant_id": "tenant_123",
            "user_id": "user_1",
            "roles": ["support"],
            "query": "How long do refunds take?",
        },
    )
    assert chat_resp.status_code == 200
    body = chat_resp.json()
    assert body["citations"]
    assert "indexed context" in body["answer"]


def test_acl_filtering_blocks_wrong_role():
    client = TestClient(create_app())
    client.post(
        "/documents/ingest",
        json={
            "document_id": "finance-policy",
            "tenant_id": "tenant_123",
            "acl": ["finance"],
            "text": "Finance reimbursement policy is 15 days.",
        },
    )
    chat_resp = client.post(
        "/chat",
        json={
            "tenant_id": "tenant_123",
            "user_id": "user_1",
            "roles": ["support"],
            "query": "What is the reimbursement policy?",
        },
    )
    assert chat_resp.status_code == 200
    assert chat_resp.json()["citations"] == []


def test_chat_stream_emits_answer_events():
    client = TestClient(create_app())
    client.post(
        "/documents/ingest",
        json={
            "document_id": "refund-policy-v1",
            "tenant_id": "tenant_123",
            "acl": ["support"],
            "text": "Refunds are processed within 7 business days.",
        },
    )

    stream_resp = client.post(
        "/chat/stream",
        json={
            "tenant_id": "tenant_123",
            "user_id": "user_1",
            "roles": ["support"],
            "query": "How long do refunds take?",
        },
    )

    assert stream_resp.status_code == 200
    assert stream_resp.headers["content-type"].startswith("text/event-stream")
    events = [_parse_sse_frame(frame) for frame in stream_resp.text.strip().split("\n\n")]
    assert events[0]["type"] == "session"
    assert any(event["type"] == "delta" for event in events)
    assert any(event["type"] == "citations" and event["citations"] for event in events)
    assert events[-1]["type"] == "done"


def _parse_sse_frame(frame: str):
    event_type = "message"
    data = "{}"
    for line in frame.splitlines():
        if line.startswith("event:"):
            event_type = line.removeprefix("event:").strip()
        if line.startswith("data:"):
            data = line.removeprefix("data:").strip()
    return {"type": event_type, **json.loads(data)}
