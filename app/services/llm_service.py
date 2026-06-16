import json

import boto3


class LLMService:
    def __init__(self, model_id: str, region_name: str, use_bedrock: bool):
        self.model_id = model_id
        self.use_bedrock = use_bedrock
        self.client = boto3.client("bedrock-runtime", region_name=region_name) if use_bedrock else None

    def generate(self, prompt: str) -> str:
        if not self.use_bedrock:
            return self._local_grounded_answer(prompt)

        response = self.client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.1, "maxTokens": 800},
        )
        return response["output"]["message"]["content"][0]["text"]

    def _local_grounded_answer(self, prompt: str) -> str:
        # Test/local fallback: returns compact extractive answer.
        marker = "Context:"
        if marker in prompt:
            context = prompt.split(marker, 1)[1].split("Question:", 1)[0].strip()
            return "Based on the indexed context: " + context[:700]
        return "Local mode answer unavailable. Enable USE_BEDROCK=true for real LLM generation."
