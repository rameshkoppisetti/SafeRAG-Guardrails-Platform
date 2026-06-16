import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PiiScanResult:
    redacted_text: str
    has_pii: bool
    types: list[str]


class PiiScanner:
    EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_IN = re.compile(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)")
    CREDIT_CARD = re.compile(r"(?<!\d)(?:\d[ -]*?){13,16}(?!\d)")
    PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

    def scan_and_redact(self, text: str) -> PiiScanResult:
        redacted = text
        detected: list[str] = []

        patterns = [
            ("EMAIL", self.EMAIL, "[EMAIL_REDACTED]"),
            ("PHONE", self.PHONE_IN, "[PHONE_REDACTED]"),
            ("CREDIT_CARD", self.CREDIT_CARD, "[CARD_REDACTED]"),
            ("PAN", self.PAN, "[PAN_REDACTED]"),
        ]
        for pii_type, pattern, replacement in patterns:
            if pattern.search(redacted):
                detected.append(pii_type)
                redacted = pattern.sub(replacement, redacted)

        return PiiScanResult(
            redacted_text=redacted,
            has_pii=bool(detected),
            types=detected,
        )
