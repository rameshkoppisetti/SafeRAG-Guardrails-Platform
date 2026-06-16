from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_ingestion import router as ingestion_router
from app.api.routes_sessions import router as sessions_router
from app.core.config import get_settings
from app.repositories.audit_repository import InMemoryAuditRepository
from app.repositories.langchain_vector_repository import LangChainVectorRepositoryFactory
from app.repositories.session_repository import SessionRepositoryFactory
from app.services.audit_service import AuditService
from app.services.guardrail_service import GuardrailService
from app.services.ingestion_service import IngestionService
from app.services.langchain_embedding_service import LangChainEmbeddingFactory
from app.services.llm_service import LLMService
from app.services.pii_scanner import PiiScanner
from app.services.rag_service import RAGService
from app.services.secret_scanner import SecretScanner


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.4.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    audit_repo = InMemoryAuditRepository()
    session_repo = SessionRepositoryFactory.create(
        backend=settings.session_backend,
        postgres_connection=settings.postgres_connection,
    )
    audit = AuditService(audit_repo)

    guardrail = GuardrailService(
        guardrail_id=settings.bedrock_guardrail_id,
        guardrail_version=settings.bedrock_guardrail_version,
        region_name=settings.aws_region,
        use_bedrock=settings.use_bedrock,
    )
    embeddings = LangChainEmbeddingFactory.create(
        use_bedrock=settings.use_bedrock,
        model_id=settings.bedrock_embedding_model_id,
        region_name=settings.aws_region,
    )
    vector_repo = LangChainVectorRepositoryFactory.create(
        backend=settings.vector_backend,
        embeddings=embeddings,
        pgvector_connection=settings.pgvector_connection,
        pgvector_collection=settings.pgvector_collection,
        pinecone_api_key=settings.pinecone_api_key,
        pinecone_index_name=settings.pinecone_index_name,
        pinecone_cloud=settings.pinecone_cloud,
        pinecone_region=settings.pinecone_region,
        pinecone_dimension=settings.pinecone_dimension,
    )
    llm = LLMService(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        use_bedrock=settings.use_bedrock,
    )

    app.state.ingestion_service = IngestionService(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        secret_scanner=SecretScanner(),
        pii_scanner=PiiScanner(),
        guardrail=guardrail,
        vector_repo=vector_repo,
        audit=audit,
    )
    app.state.rag_service = RAGService(
        guardrail=guardrail,
        vector_repo=vector_repo,
        session_repo=session_repo,
        llm=llm,
        audit=audit,
        default_top_k=settings.vector_top_k,
    )
    app.state.audit_repo = audit_repo
    app.state.session_repo = session_repo
    app.state.vector_repo = vector_repo

    app.include_router(ingestion_router)
    app.include_router(chat_router)
    app.include_router(sessions_router)

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "vector_backend": settings.vector_backend,
            "indexed_chunks": vector_repo.count(),
        }

    return app


app = create_app()
