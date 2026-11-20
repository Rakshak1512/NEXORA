import re
from typing import Tuple, Dict, Any, List

class LocalDataRedactor:
    """
    LOCAL DATA REDACTOR
    Guarantees that no raw secret, password, token, or connection string
    ever leaves the customer's on-premises / local perimeter.
    """
    PATTERNS = [
        (re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]+)["\']?'), "[REDACTED_PASSWORD]"),
        (re.compile(r'(?i)(bearer\s+[a-zA-Z0-9_\-\.]{20,})'), "[REDACTED_BEARER_TOKEN]"),
        (re.compile(r'(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?'), "[REDACTED_API_KEY]"),
        (re.compile(r'AKIA[0-9A-Z]{16}'), "[REDACTED_AWS_ACCESS_KEY]"),
        (re.compile(r'ghp_[a-zA-Z0-9]{36}'), "[REDACTED_GITHUB_TOKEN]"),
        (re.compile(r'(?i)(postgres|mysql|mongodb|redis):\/\/[^:\s]+:([^@\s]+)@'), "[REDACTED_CONN_STRING]"),
        (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), "[REDACTED_EMAIL_ADDRESS]"),
        (re.compile(r'(-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----)'), "[REDACTED_PRIVATE_KEY]"),
    ]

    @classmethod
    def redact_text(cls, text: str) -> Tuple[str, List[str]]:
        """Redacts sensitive strings and records what type of secrets were caught."""
        redacted_types = []
        result = text
        for pattern, replacement in cls.PATTERNS:
            if pattern.search(result):
                redacted_types.append(replacement.strip("[]"))
                result = pattern.sub(replacement, result)
        return result, redacted_types

    @classmethod
    def sanitize_dictionary(cls, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int, List[str]]:
        """
        Recursively scans dictionaries, scrubbing known secret fields
        and redacting sensitive pattern matches in string values.
        """
        sanitized = {}
        redaction_count = 0
        detected_types = []

        sensitive_key_names = {
            'password', 'secret', 'api_key', 'private_key',
            'credentials', 'cert', 'ssn', 'authorization'
        }

        for k, v in data.items():
            k_lower = str(k).lower()
            
            # If key name itself indicates sensitive credential and it is scalar
            if any(s in k_lower for s in sensitive_key_names) and not isinstance(v, (dict, list)):
                sanitized[k] = "[REDACTED_SENSITIVE_KEY]"
                redaction_count += 1
                detected_types.append(f"key:{k}")
                continue

            if isinstance(v, str):
                cleaned, caught = cls.redact_text(v)
                if caught:
                    redaction_count += len(caught)
                    detected_types.extend(caught)
                sanitized[k] = cleaned
            elif isinstance(v, dict):
                sub_clean, sub_count, sub_caught = cls.sanitize_dictionary(v)
                sanitized[k] = sub_clean
                redaction_count += sub_count
                detected_types.extend(sub_caught)
            elif isinstance(v, list):
                clean_list = []
                for item in v:
                    if isinstance(item, str):
                        c, caught = cls.redact_text(item)
                        if caught:
                            redaction_count += len(caught)
                            detected_types.extend(caught)
                        clean_list.append(c)
                    elif isinstance(item, dict):
                        c_dict, c_cnt, c_caught = cls.sanitize_dictionary(item)
                        redaction_count += c_cnt
                        detected_types.extend(c_caught)
                        clean_list.append(c_dict)
                    else:
                        clean_list.append(item)
                sanitized[k] = clean_list
            else:
                sanitized[k] = v

        return sanitized, redaction_count, list(set(detected_types))
