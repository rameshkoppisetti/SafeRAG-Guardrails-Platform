from dataclasses import dataclass

import boto3


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    text: str
    action: str
    raw: dict | None = None


class GuardrailService:
    def __init__(
        self,
        guardrail_id: str | None,
        guardrail_version: str,
        region_name: str,
        use_bedrock: bool,
    ):
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.use_bedrock = use_bedrock and bool(guardrail_id)
        self.client = (
            boto3.client("bedrock-runtime", region_name=region_name) if self.use_bedrock else None
        )

    def validate_input(self, text: str) -> GuardrailResult:
        return self._apply(text=text, source="INPUT")

    def validate_output(self, text: str) -> GuardrailResult:
        return self._apply(text=text, source="OUTPUT")

    def _apply(self, text: str, source: str) -> GuardrailResult:
        if not self.use_bedrock:
            return GuardrailResult(allowed=True, text=text, action="SKIPPED_LOCAL_MODE")

        response = self.client.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source=source,
            content=[{"text": {"text": text}}],
        )
        action = response.get("action", "NONE")

        if action == "GUARDRAIL_INTERVENED":
            outputs = response.get("outputs") or []
            guarded_text = outputs[0].get("text") if outputs else "I can't help with that request."
            return GuardrailResult(False, guarded_text, action, response)

        outputs = response.get("outputs") or []
        safe_text = outputs[0].get("text") if outputs else text
        return GuardrailResult(True, safe_text, action, response)
