import pytest
from app.redactor import LocalDataRedactor

def test_password_redaction():
    text = "Connecting with password=SuperSecretPassword123! to server"
    cleaned, caught = LocalDataRedactor.redact_text(text)
    assert "[REDACTED_PASSWORD]" in cleaned
    assert "SuperSecretPassword123!" not in cleaned

def test_bearer_token_redaction():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake_token_example"
    cleaned, caught = LocalDataRedactor.redact_text(text)
    assert "[REDACTED_BEARER_TOKEN]" in cleaned
    assert "fake_token_example" not in cleaned

def test_aws_key_redaction():
    text = "Access key is AKIAIOSFODNN7EXAMPLE for backup S3 bucket"
    cleaned, caught = LocalDataRedactor.redact_text(text)
    assert "[REDACTED_AWS_ACCESS_KEY]" in cleaned
    assert "AKIAIOSFODNN7EXAMPLE" not in cleaned

def test_connection_string_redaction():
    text = "postgres://cynera_admin:MyP@ssw0rd!@10.0.1.5:5432/core_db"
    cleaned, caught = LocalDataRedactor.redact_text(text)
    assert "[REDACTED_CONN_STRING]" in cleaned
    assert "MyP@ssw0rd!" not in cleaned

def test_sanitize_nested_dictionary():
    raw_dict = {
        "cpu_pct": 45.2,
        "database": {
            "conn": "postgres://user:Secret123@localhost/db",
            "password": "ClearTextPassword!"
        },
        "tokens": ["Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.long_fake_token_value_sample"]
    }
    sanitized, count, caught_types = LocalDataRedactor.sanitize_dictionary(raw_dict)
    assert count >= 3
    assert sanitized["database"]["password"] == "[REDACTED_SENSITIVE_KEY]"
    assert "[REDACTED_CONN_STRING]" in sanitized["database"]["conn"]
    assert "[REDACTED_BEARER_TOKEN]" in sanitized["tokens"][0]

