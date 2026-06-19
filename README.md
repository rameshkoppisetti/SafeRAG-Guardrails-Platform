# SafeRAG Guardrails Platform

Production-grade reference implementation for a safe RAG backend using FastAPI, AWS Bedrock Guardrails, ingestion-time safety checks, vector retrieval, ACL-aware search, and output validation.

## Why this project exists

Most RAG demos directly embed raw documents into a vector database. That is risky in production because secrets, PII, unsafe content, or unauthorized tenant data can become retrievable later. This project adds safety before indexing, during retrieval, and before returning final answers.

## Architecture

```text
Document Upload / Sync
   ↓
Parse text
   ↓
Chunk text
   ↓
Secret scanner
   ↓
PII scanner / redactor
   ↓
AWS Bedrock Guardrails ApplyGuardrail(INPUT)
   ↓
Embedding generation
   ↓
Vector DB with tenant + ACL metadata

User Query + session_id
   ↓
Session memory lookup
   ↓
AWS Bedrock Guardrails ApplyGuardrail(INPUT)
   ↓
Query embedding
   ↓
ACL-aware vector retrieval
   ↓
Grounded prompt
   ↓
LLM generation
   ↓
AWS Bedrock Guardrails ApplyGuardrail(OUTPUT)
   ↓
Answer + citations
```

For a component-level HLD with request flows, see [docs/hld.md](docs/hld.md).
For interview talking points and tradeoffs, see [docs/interview-notes.md](docs/interview-notes.md).

## Features

- FastAPI backend
- Ingestion-time safety layer
- PII redaction for email, phone, PAN, and card-like numbers
- Secret scanner for AWS keys, private keys, and token-like values
- AWS Bedrock Guardrails wrapper
- AWS Bedrock Titan Embeddings wrapper
- AWS Bedrock Converse LLM wrapper
- Local deterministic embedding fallback for dev/test
- In-memory vector repository for local runs
- Tenant and ACL-aware retrieval
- Citation-aware RAG response
- Multi-session chat memory per tenant/user/session
- Postgres-backed persistent session memory
- Session APIs to create, list, and inspect message history
- Audit events for blocked/indexed chunks and responses
- Dockerfile and docker-compose
- Pytest coverage for scanners, chunking, ingestion, chat, and ACL filtering

## Local quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

The default `.env` uses in-memory vector and session storage so the API can run without
Postgres. To test persistent session memory locally, start Postgres first:

```bash
docker compose up -d pgvector
SESSION_BACKEND=postgres uvicorn app.main:app --reload
```

## Run demo

```bash
python scripts/demo.py
```

## Enable AWS Bedrock

Set `.env`:

```env
USE_BEDROCK=true
AWS_REGION=us-east-1
BEDROCK_GUARDRAIL_ID=your_guardrail_id
BEDROCK_GUARDRAIL_VERSION=1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

The app uses `bedrock-runtime.apply_guardrail`, `bedrock-runtime.invoke_model` for embeddings, and `bedrock-runtime.converse` for answer generation.

## Example: ingest document

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": "refund-policy-v1",
    "tenant_id": "tenant_123",
    "acl": ["support"],
    "text": "Refunds are processed within 7 business days. Contact support for refund status."
  }'
```

## Example: chat

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id": "tenant_123",
    "user_id": "user_1",
    "roles": ["support"],
    "query": "How long do refunds take?"
  }'
```

## Production evolution

Replace the in-memory vector repository with one of:

- Amazon OpenSearch Serverless vector search
- pgvector
- Pinecone
- Weaviate
- Milvus

Add:

- Persistent audit DB
- S3 document storage
- Async ingestion workers
- Dead-letter queue for failed documents
- Reranking layer
- Contextual grounding checks
- Per-tenant encryption keys
- OIDC/JWT authentication
- Role-based authorization middleware

## Interview talking point

> I would keep memory isolated by tenant, user, and session. Short-term memory helps resolve follow-up questions, but retrieval still remains grounded in ACL-filtered indexed documents. I would not directly dump raw documents into vectors or OpenSearch. I would add an ingestion safety layer before embedding: parse, chunk, scan for PII/secrets, apply Bedrock Guardrails, redact or block unsafe chunks, attach ACL metadata, then index only sanitized text. At query time, retrieval is filtered by tenant and ACL. At response time, output guardrails and grounding checks are applied.
