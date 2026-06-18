from dataclasses import dataclass
from typing import Iterable

from app.core.langchain_compat import Document, Embeddings


@dataclass(frozen=True)
class LangChainSearchResult:
    document: Document
    score: float


class LangChainVectorRepository:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self._local_count = 0

    def add_documents(self, documents: list[Document], ids: list[str]) -> None:
        self.vector_store.add_documents(documents=documents, ids=ids)
        self._local_count += len(documents)

    def search(self, query: str, tenant_id: str, roles: list[str], top_k: int) -> list[LangChainSearchResult]:
        filter_query = self._build_filter(tenant_id, roles)
        try:
            results = self.vector_store.similarity_search_with_score(query=query, k=top_k, filter=filter_query)
        except Exception:
            results = self._search_and_authorize(query, tenant_id, roles, top_k)
        else:
            if not results:
                results = self._search_and_authorize(query, tenant_id, roles, top_k)
        return [LangChainSearchResult(document=doc, score=float(score)) for doc, score in results]

    def count(self) -> int:
        return self._local_count

    def _build_filter(self, tenant_id: str, roles: list[str]) -> dict:
        acl_values = roles or ["__public__"]
        return {"$and": [{"tenant_id": {"$eq": tenant_id}}, {"acl": {"$in": acl_values}}]}

    def _is_authorized(self, doc: Document, tenant_id: str, roles: Iterable[str]) -> bool:
        metadata = doc.metadata or {}
        if metadata.get("tenant_id") != tenant_id:
            return False
        acl = metadata.get("acl", [])
        if isinstance(acl, str):
            acl = [acl]
        if not acl or "__public__" in acl:
            return True
        return bool(set(roles).intersection(set(acl)))

    def _search_and_authorize(
        self,
        query: str,
        tenant_id: str,
        roles: Iterable[str],
        top_k: int,
    ):
        raw_results = self.vector_store.similarity_search_with_score(query=query, k=top_k * 3)
        return [(doc, score) for doc, score in raw_results if self._is_authorized(doc, tenant_id, roles)][:top_k]


class LocalInMemoryVectorStore:
    def __init__(self, embeddings: Embeddings):
        self.embeddings = embeddings
        self._docs: dict[str, Document] = {}
        self._vectors: dict[str, list[float]] = {}

    def add_documents(self, documents: list[Document], ids: list[str]) -> None:
        vectors = self.embeddings.embed_documents([doc.page_content for doc in documents])
        for doc_id, doc, vector in zip(ids, documents, vectors):
            self._docs[doc_id] = doc
            self._vectors[doc_id] = vector

    def similarity_search_with_score(self, query: str, k: int, filter: dict | None = None):
        import numpy as np

        q = np.asarray(self.embeddings.embed_query(query), dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        results = []
        for doc_id, doc in self._docs.items():
            if filter and not self._matches_filter(doc.metadata or {}, filter):
                continue
            v = np.asarray(self._vectors[doc_id], dtype=np.float32)
            denom = q_norm * np.linalg.norm(v)
            if denom == 0:
                continue
            score = float(np.dot(q, v) / denom)
            results.append((doc, score))
        results.sort(key=lambda item: item[1], reverse=True)
        return results[:k]

    def _matches_filter(self, metadata: dict, filter_query: dict) -> bool:
        if not filter_query:
            return True
        if "$and" in filter_query:
            return all(self._matches_filter(metadata, item) for item in filter_query["$and"])
        for key, condition in filter_query.items():
            value = metadata.get(key)
            if isinstance(condition, dict):
                if "$eq" in condition and value != condition["$eq"]:
                    return False
                if "$in" in condition:
                    expected = set(condition["$in"])
                    actual = value if isinstance(value, list) else [value]
                    if not expected.intersection(set(actual)):
                        return False
            elif value != condition:
                return False
        return True


class LangChainVectorRepositoryFactory:
    @staticmethod
    def create(
        backend: str,
        embeddings: Embeddings,
        pgvector_connection: str,
        pgvector_collection: str,
        pinecone_api_key: str | None,
        pinecone_index_name: str,
        pinecone_cloud: str,
        pinecone_region: str,
        pinecone_dimension: int,
    ) -> LangChainVectorRepository:
        backend = backend.lower()
        if backend == "memory":
            try:
                from langchain_core.vectorstores import InMemoryVectorStore
                return LangChainVectorRepository(InMemoryVectorStore(embeddings))
            except ModuleNotFoundError:
                return LangChainVectorRepository(LocalInMemoryVectorStore(embeddings))
        if backend == "pgvector":
            from langchain_postgres import PGVector
            store = PGVector(
                embeddings=embeddings,
                collection_name=pgvector_collection,
                connection=pgvector_connection,
                use_jsonb=True,
            )
            return LangChainVectorRepository(store)
        if backend == "pinecone":
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY is required when VECTOR_BACKEND=pinecone")
            from pinecone import Pinecone, ServerlessSpec
            from langchain_pinecone import PineconeVectorStore
            pc = Pinecone(api_key=pinecone_api_key)
            if not pc.has_index(pinecone_index_name):
                pc.create_index(
                    name=pinecone_index_name,
                    dimension=pinecone_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud=pinecone_cloud, region=pinecone_region),
                )
            index = pc.Index(pinecone_index_name)
            return LangChainVectorRepository(PineconeVectorStore(index=index, embedding=embeddings))
        raise ValueError(f"Unsupported VECTOR_BACKEND={backend}. Use memory, pgvector, or pinecone.")
