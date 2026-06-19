# SafeRAG Guardrails Platform Interview Notes

## One-Minute Pitch

SafeRAG is a production-style RAG platform that focuses on safety before and after retrieval. It does not blindly embed raw documents. During ingestion it chunks documents, scans for secrets, redacts PII, applies AWS Bedrock Guardrails, and stores only accepted chunks in pgvector with tenant and ACL metadata. During chat it validates the user query, retrieves only authorized chunks, generates a grounded answer with Bedrock, validates the output, streams the response to the UI, and persists chat memory in Postgres.

## Why This Project Matters

Most RAG demos optimize only for retrieval quality. In production, the bigger risks are data leakage, unsafe content, prompt injection, and stale or unauthorized context. This project demonstrates how to build a safer RAG workflow with guardrails at ingestion time, retrieval time, and response time.

## Core Architecture

- React frontend for document ingestion, identity/ACL selection, session selection, and streaming chat.
- FastAPI backend exposing ingestion, session, health, normal chat, and streaming chat APIs.
- AWS Bedrock Guardrails for input and output safety checks.
- AWS Bedrock Titan Text Embeddings V2 for document/query embeddings.
- AWS Bedrock Amazon Nova Lite for answer generation.
- Postgres/pgvector for persistent vector storage.
- Postgres for persistent chat sessions and messages.
- In-memory audit store for local safety-event tracking.
- Docker Compose for local Postgres/pgvector.

## Key Design Decisions

### Scan Before Embedding

Documents are scanned before embedding because vectors can preserve sensitive information semantically. If secrets or PII are embedded first, they can be retrieved later even if the original document is deleted or hidden. This project blocks secret-containing chunks and redacts PII before indexing.

### Guardrails At Multiple Points

Guardrails are applied at three important points:

- Ingestion input: blocks unsafe document chunks before indexing.
- User query input: blocks unsafe user prompts before retrieval/generation.
- Model output: blocks unsafe answers before returning to the user.

This layered approach reduces reliance on a single safety check.

### Tenant And ACL Metadata

Each chunk is stored with:

- `tenant_id`
- `acl`
- `document_id`
- `chunk_id`

Retrieval enforces tenant and role checks so users only receive context they are authorized to see. The app also has a fallback authorization check in Python in case the vector-store metadata filter behaves differently across backends.

### pgvector Instead Of Memory

The app supports in-memory vector storage for tests, but pgvector is used for realistic local development because embeddings persist across API restarts and can be inspected in DBeaver. This also makes the storage model closer to production.

### Streaming Chat

The frontend uses a POST-based streaming endpoint (`/chat/stream`) that returns Server-Sent Events frames. This keeps the request body structured while allowing progressive UI updates. The normal `/chat` endpoint remains available for simple clients and tests.

## Main Flows

### Ingestion

1. User submits document text, tenant ID, and ACL.
2. Backend splits text into chunks.
3. Each chunk is scanned for secrets.
4. PII is detected and redacted.
5. Bedrock Guardrails validate the chunk.
6. Accepted chunks are embedded.
7. Text, embedding, and metadata are stored in pgvector.

### Chat

1. User submits tenant ID, user ID, roles, session ID, and query.
2. Backend gets or creates a session.
3. Bedrock Guardrails validate the query.
4. Query is embedded.
5. pgvector retrieves relevant chunks.
6. App applies tenant/ACL authorization.
7. Prompt is built with conversation memory and retrieved context.
8. Bedrock model generates an answer.
9. Bedrock Guardrails validate the answer.
10. Messages are persisted in Postgres.
11. Answer deltas and citations stream to the frontend.

## What I Would Improve Next

- Add JWT/OIDC authentication and map identity claims to tenant and roles.
- Add structured logs with request IDs, latency, token usage, and Bedrock cost estimates.
- Add RAG evaluation scripts for retrieval hit rate and answer correctness.
- Add GitHub Actions CI for backend tests and frontend type checks.
- Add production audit persistence instead of in-memory audit storage.
- Add admin APIs for deleting documents and re-indexing collections.
- Add reranking for better citation precision.
- Add prompt-injection detection and context-grounding checks beyond basic guardrails.
- Add deployment docs for ECS/Fargate or Kubernetes.

## Interview Questions To Expect

### Why not embed the raw document first and filter later?

Because sensitive content can leak through vector retrieval even if the raw document is later hidden. The safer approach is to sanitize or block content before embedding.

### How do you prevent cross-tenant data leakage?

Every chunk has tenant and ACL metadata. Retrieval uses metadata filters and then the app performs a second tenant/ACL authorization check before sending context to the model.

### Why use Bedrock Guardrails?

Guardrails provide managed policy enforcement for unsafe inputs and outputs. They are useful as a centralized safety layer around both ingestion and generation.

### Why keep conversation memory separate from retrieved context?

Memory helps resolve follow-up references, but answers must still be grounded in authorized retrieved documents. The prompt explicitly treats retrieved context as data and asks the model to answer only from that context.

### What happens if Bedrock is unavailable?

The app has local-mode fallbacks for development and tests. In production, failures should return controlled API errors, be logged with request IDs, and trigger retries or circuit-breaking depending on the operation.

### What makes this more production-ready than a basic RAG demo?

It includes safety scanning, guardrails, tenant/ACL retrieval, persistent vector storage, persistent sessions, streaming responses, Dockerized infrastructure, tests, and architecture documentation.

## Demo Script

1. Start Postgres:

```bash
docker compose up -d pgvector
```

2. Start backend:

```bash
uvicorn app.main:app --reload
```

3. Start frontend:

```bash
cd frontend
npm run dev
```

4. Ingest a refund policy:

```text
Refunds are processed within 7 business days. Contact support for refund status.
```

5. Ask:

```text
How long do refunds take?
```

Expected answer:

```text
Refunds are processed within 7 business days.
```

6. Show DBeaver tables:

- `chat_sessions`
- `chat_messages`
- `langchain_pg_collection`
- `langchain_pg_embedding`

7. Ask unsafe prompts and show Guardrails blocking responses.
