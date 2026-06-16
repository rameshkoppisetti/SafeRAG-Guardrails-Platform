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
