from app.services.pii_scanner import PiiScanner
from app.services.secret_scanner import SecretScanner


def test_pii_scanner_redacts_email_phone_pan():
    result = PiiScanner().scan_and_redact("Email a@b.com phone 9876543210 PAN ABCDE1234F")
    assert result.has_pii
    assert "[EMAIL_REDACTED]" in result.redacted_text
    assert "[PHONE_REDACTED]" in result.redacted_text
    assert "[PAN_REDACTED]" in result.redacted_text


def test_secret_scanner_detects_aws_key():
    result = SecretScanner().scan("key = AKIA1234567890ABCDEF")
    assert result.has_secret
    assert "AWS_ACCESS_KEY" in result.types
