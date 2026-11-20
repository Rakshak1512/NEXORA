import re
import copy
from typing import Any, Dict, List, Union, Tuple

class SensitiveDataRedactor:
    """
    CYNERA MULTI-LAYER SENSITIVE DATA REDACTION ENGINE (Layer 4 & 6)
    Identifies, classifies, and redacts sensitive credentials, tokens, PII,
    and secrets before persistence, external egress, or submission to AI models.
    """

    PATTERNS = [
        # Bearer & JWT Tokens
        (r'Bearer\s+([A-Za-z0-9\-_\.~+/=]+)', r'Bearer [REDACTED_BEARER_TOKEN]'),
        (r'eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}', r'[REDACTED_JWT_TOKEN]'),

        # Database Connection Strings
        (r'postgres(ql)?://([^:]+):([^@]+)@([^/:]+)(:\d+)?/([^\s\?]+)', r'postgresql://[REDACTED_USER]:[REDACTED_PASSWORD]@[REDACTED_HOST]:\5/\6'),
        (r'mysql://([^:]+):([^@]+)@([^/:]+)(:\d+)?/([^\s\?]+)', r'mysql://[REDACTED_USER]:[REDACTED_PASSWORD]@[REDACTED_HOST]:\5/\6'),
        (r'mongodb(\+srv)?://([^:]+):([^@]+)@([^\s/]+)', r'mongodb://[REDACTED_USER]:[REDACTED_PASSWORD]@[REDACTED_HOST]'),

        # Cloud Credentials & Secret Keys
        (r'(AKIA|ASIA)[0-9A-Z]{16}', r'[REDACTED_AWS_ACCESS_KEY]'),
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----', r'[REDACTED_PRIVATE_KEY]'),
        (r'sb_secret_[A-Za-z0-9\-_]{32,}', r'[REDACTED_SUPABASE_SECRET_KEY]'),
        (r're_[A-Za-z0-9\-_]{24,}', r'[REDACTED_API_KEY]'),
        (r'cyn_live_[A-Za-z0-9\-_]{24,}', r'[REDACTED_CYNERA_LIVE_KEY]'),

        # Generic password & secret fields in query strings or logs
        (r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth)=([^\s&]+)', r'\1=[REDACTED_SECRET]'),

        # Credit Cards (Luhn candidates)
        (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', r'[REDACTED_CARD_NUMBER]'),

        # SSH Keys
        (r'ssh-(rsa|ed25519)\s+[A-Za-z0-9+/=]+', r'ssh-\1 [REDACTED_SSH_KEY]')
    ]

    SENSITIVE_KEY_NAMES = {
        'password', 'password_hash', 'passwd', 'pwd', 'secret', 'token',
        'access_token', 'refresh_token', 'auth_token', 'api_key', 'apikey',
        'auth', 'authorization', 'cookie', 'session', 'private_key',
        'client_secret', 'database_url', 'supabase_db_url', 'smtp_password'
    }

    @classmethod
    def redact_text(cls, text: str) -> Tuple[str, int]:
        """Redacts sensitive substrings from raw text. Returns (sanitized_text, redactions_count)."""
        if not text or not isinstance(text, str):
            return text, 0

        redacted = text
        total_redactions = 0
        for pattern, replacement in cls.PATTERNS:
            new_text, count = re.subn(pattern, replacement, redacted)
            if count > 0:
                total_redactions += count
                redacted = new_text

        return redacted, total_redactions

    @classmethod
    def redact_structure(cls, data: Any) -> Any:
        """Deeply walks dictionaries and lists to mask sensitive key-value pairs and strings."""
        if isinstance(data, dict):
            clean_dict = {}
            for k, v in data.items():
                k_lower = str(k).lower().strip()
                if k_lower in cls.SENSITIVE_KEY_NAMES or any(s in k_lower for s in ['password', 'secret', 'token_hash', 'credential']):
                    clean_dict[k] = "[REDACTED_CREDENTIAL]"
                else:
                    clean_dict[k] = cls.redact_structure(v)
            return clean_dict
        elif isinstance(data, list):
            return [cls.redact_structure(item) for item in data]
        elif isinstance(data, str):
            sanitized, _ = cls.redact_text(data)
            return sanitized
        return data

redactor = SensitiveDataRedactor()
