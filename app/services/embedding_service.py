import hashlib
import json

import boto3
import numpy as np


class EmbeddingService:
    def __init__(self, model_id: str, region_name: str, use_bedrock: bool):
        self.model_id = model_id
        self.use_bedrock = use_bedrock
        self.client = boto3.client("bedrock-runtime", region_name=region_name) if use_bedrock else None

    def embed(self, text: str) -> list[float]:
        if self.use_bedrock:
            body = json.dumps({"inputText": text})
            response = self.client.invoke_model(modelId=self.model_id, body=body)
            payload = json.loads(response["body"].read())
            return payload["embedding"]

        return self._deterministic_local_embedding(text)

    def _deterministic_local_embedding(self, text: str, dim: int = 384) -> list[float]:
        # Local dev fallback: deterministic hashing vector, not semantic-quality.
        vector = np.zeros(dim, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % dim
            sign = 1 if digest[4] % 2 == 0 else -1
            vector[idx] += sign
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()
