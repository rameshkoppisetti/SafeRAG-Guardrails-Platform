from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())

print(client.get("/health").json())
print(client.post("/documents/ingest", json={
    "document_id": "benefits-v1",
    "tenant_id": "tenant_123",
    "acl": ["employee"],
    "text": "Employees can claim internet reimbursement up to 2000 INR per month. Email hr@example.com for help."
}).json())
print(client.post("/chat", json={
    "tenant_id": "tenant_123",
    "user_id": "satya",
    "roles": ["employee"],
    "query": "What is the internet reimbursement limit?"
}).json())
