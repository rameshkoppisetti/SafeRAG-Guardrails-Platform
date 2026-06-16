import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretScanResult:
    has_secret: bool
    types: list[str]


class SecretScanner:
    AWS_ACCESS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
    PRIVATE_KEY = re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")
    GENERIC_TOKEN = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")

    def scan(self, text: str) -> SecretScanResult:
        detected: list[str] = []
        checks = [
            ("AWS_ACCESS_KEY", self.AWS_ACCESS_KEY),
            ("PRIVATE_KEY", self.PRIVATE_KEY),
            ("GENERIC_TOKEN", self.GENERIC_TOKEN),
        ]
        for name, pattern in checks:
            if pattern.search(text):
                detected.append(name)
        return SecretScanResult(has_secret=bool(detected), types=detected)
