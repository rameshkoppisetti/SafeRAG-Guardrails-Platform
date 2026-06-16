from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SafeRAG Guardrails Platform"
    app_env: str = "local"
    aws_region: str = "us-east-1"

    use_bedrock: bool = False
    bedrock_guardrail_id: str | None = None
    bedrock_guardrail_version: str = "DRAFT"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    vector_backend: str = "memory"  # memory | pgvector | pinecone
    vector_top_k: int = 5
    chunk_size: int = 900
    chunk_overlap: int = 120

    pgvector_connection: str = "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    pgvector_collection: str = "safe_rag_documents"

    session_backend: str = "memory"  # memory | postgres
    postgres_connection: str = "postgresql://langchain:langchain@localhost:6024/langchain"

    pinecone_api_key: str | None = None
    pinecone_index_name: str = "safe-rag-documents"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_dimension: int = 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
