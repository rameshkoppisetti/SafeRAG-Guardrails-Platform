from dataclasses import dataclass

import numpy as np

from app.models.document import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float


class InMemoryVectorRepository:
    def __init__(self):
        self._vectors: dict[str, list[float]] = {}
        self._chunks: dict[str, DocumentChunk] = {}

    def upsert(self, chunk: DocumentChunk, vector: list[float]) -> None:
        self._chunks[chunk.chunk_id] = chunk
        self._vectors[chunk.chunk_id] = vector

    def search(
        self,
        query_vector: list[float],
        tenant_id: str,
        roles: list[str],
        top_k: int,
    ) -> list[SearchResult]:
        q = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []

        results: list[SearchResult] = []
        role_set = set(roles)

        for chunk_id, vector in self._vectors.items():
            chunk = self._chunks[chunk_id]
            if chunk.tenant_id != tenant_id:
                continue
            if chunk.acl and not role_set.intersection(chunk.acl):
                continue

            v = np.asarray(vector, dtype=np.float32)
            denom = q_norm * np.linalg.norm(v)
            if denom == 0:
                continue
            score = float(np.dot(q, v) / denom)
            results.append(SearchResult(chunk=chunk, score=score))

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self._chunks)
