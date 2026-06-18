from app.core.langchain_compat import Document
from app.repositories.langchain_vector_repository import LangChainVectorRepository


class FilterMissVectorStore:
    def __init__(self):
        self.document = Document(
            page_content="Refunds are processed within 7 business days.",
            metadata={
                "document_id": "refund-policy-v1",
                "chunk_id": "refund-policy-v1:0",
                "tenant_id": "tenant_123",
                "acl": ["support", "employee"],
            },
        )

    def similarity_search_with_score(self, query, k, filter=None):
        if filter:
            return []
        return [(self.document, 0.91)]


def test_search_falls_back_to_app_acl_filter_when_store_filter_misses_array_acl():
    repo = LangChainVectorRepository(FilterMissVectorStore())

    results = repo.search(
        query="How long do refunds take?",
        tenant_id="tenant_123",
        roles=["support"],
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].document.metadata["document_id"] == "refund-policy-v1"


def test_search_fallback_still_blocks_unauthorized_roles():
    repo = LangChainVectorRepository(FilterMissVectorStore())

    results = repo.search(
        query="How long do refunds take?",
        tenant_id="tenant_123",
        roles=["finance"],
        top_k=5,
    )

    assert results == []
