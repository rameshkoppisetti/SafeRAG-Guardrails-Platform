import hashlib
from typing import List

import numpy as np
from app.core.langchain_compat import Embeddings


class LocalHashEmbeddings(Embeddings):
    """Deterministic local embeddings for tests/dev only, not semantic-quality."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1 if digest[4] % 2 == 0 else -1
            vector[idx] += sign
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


class LangChainEmbeddingFactory:
    @staticmethod
    def create(use_bedrock: bool, model_id: str, region_name: str) -> Embeddings:
        if not use_bedrock:
            return LocalHashEmbeddings()
        from langchain_aws import BedrockEmbeddings
        return BedrockEmbeddings(model_id=model_id, region_name=region_name)
