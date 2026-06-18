# SafeRAG Guardrails Platform HLD

## System Components

```mermaid
flowchart LR
    User["User / Browser"] --> UI["React UI<br/>Vite frontend"]
    UI --> API["FastAPI backend<br/>REST + POST streaming chat"]

    subgraph Backend["Backend services"]
        API --> Ingestion["IngestionService<br/>chunk, scan, guard, embed"]
        API --> RAG["RAGService<br/>retrieve, prompt, answer"]
        API --> Sessions["SessionRepository<br/>chat memory"]
        API --> Audit["AuditService<br/>safety events"]

        Ingestion --> SecretScanner["SecretScanner"]
        Ingestion --> PiiScanner["PiiScanner"]
        Ingestion --> Guardrails["GuardrailService"]
        RAG --> Guardrails
        RAG --> LLM["LLMService"]
        RAG --> VectorRepo["LangChainVectorRepository"]
        Ingestion --> VectorRepo
    end

    subgraph AWS["AWS Bedrock"]
        Guardrails --> BedrockGuardrails["Bedrock Guardrails<br/>input/output policy checks"]
        LLM --> BedrockModel["Bedrock model<br/>Amazon Nova Lite"]
        Embeddings["Bedrock embeddings<br/>Titan Text Embeddings V2"]
    end

    VectorRepo --> Embeddings
    VectorRepo --> PgVector["Postgres + pgvector<br/>langchain_pg_collection<br/>langchain_pg_embedding"]
    Sessions --> Postgres["Postgres<br/>chat_sessions<br/>chat_messages"]
    Audit --> MemoryAudit["In-memory audit store"]

    API --> Docker["Docker Compose<br/>pgvector service"]
    Docker --> PgVector
    Docker --> Postgres
```

## Ingestion Flow

```mermaid
sequenceDiagram
    participant UI as React UI
    participant API as FastAPI
    participant ING as IngestionService
    participant SCAN as PII/Secret scanners
    participant GR as Bedrock Guardrails
    participant EMB as Bedrock Embeddings
    participant PG as Postgres/pgvector

    UI->>API: POST /documents/ingest
    API->>ING: ingest(document_id, tenant_id, acl, text)
    ING->>ING: split document into chunks
    ING->>SCAN: scan secrets and redact PII
    ING->>GR: ApplyGuardrail(INPUT)
    GR-->>ING: allowed or blocked text
    ING->>EMB: embed accepted chunks
    EMB-->>ING: vectors
    ING->>PG: store chunk text, metadata, embeddings
    API-->>UI: accepted_chunks / blocked_chunks
```

## Chat Flow

```mermaid
sequenceDiagram
    participant UI as React UI
    participant API as FastAPI
    participant RAG as RAGService
    participant GR as Bedrock Guardrails
    participant PG as Postgres/pgvector
    participant LLM as Bedrock model
    participant S as Postgres sessions

    UI->>API: POST /chat/stream
    API->>RAG: answer tenant/user/roles/query
    RAG->>S: get or create session
    RAG->>GR: ApplyGuardrail(INPUT query)
    GR-->>RAG: safe query or block response
    RAG->>PG: similarity search + tenant/ACL authorization
    PG-->>RAG: top matching chunks
    RAG->>LLM: grounded prompt with context
    LLM-->>RAG: draft answer
    RAG->>GR: ApplyGuardrail(OUTPUT answer)
    GR-->>RAG: safe answer or block response
    RAG->>S: persist user and assistant messages
    RAG-->>API: answer + citations
    API-->>UI: stream session, delta, citations, done events
```

## Runtime Configuration

- `USE_BEDROCK=true` enables Bedrock Guardrails, embeddings, and chat model calls.
- `AWS_REGION=eu-north-1` selects the Bedrock region.
- `BEDROCK_GUARDRAIL_ID` and `BEDROCK_GUARDRAIL_VERSION` select the guardrail.
- `BEDROCK_MODEL_ID=amazon.nova-lite-v1:0` is used for answer generation.
- `BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0` is used for embeddings.
- `VECTOR_BACKEND=pgvector` stores document chunks and embeddings in Postgres/pgvector.
- `SESSION_BACKEND=postgres` stores chat sessions and messages in Postgres.
