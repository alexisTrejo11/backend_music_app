import logging
import re


class InfoOnlyFilter(logging.Filter):
    """Filter INFO level logs only"""

    def filter(self, record):
        return record.levelno == logging.INFO


class ExcludeSensitiveFilter(logging.Filter):
    """Filter sensitive data from logs"""

    SENSITIVE_PATTERNS = [
        r"password[^=]*=([^&\s]+)",
        r"token[^=]*=([^&\s]+)",
        r"api_key[^=]*=([^&\s]+)",
        r"secret[^=]*=([^&\s]+)",
        r"credit_card[^=]*=([^&\s]+)",
        r"cc_number[^=]*=([^&\s]+)",
        r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Credit Cards
        r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",  # SSN
    ]

    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(
                    pattern, "[FILTERED]", record.msg, flags=re.IGNORECASE
                )

        if isinstance(record.args, dict):
            for key in ["password", "token", "secret", "api_key"]:
                if key in record.args:
                    record.args[key] = "[FILTERED]"

        return True


class ModuleFilter(logging.Filter):
    """Filter logs by module"""

    def __init__(self, module_name=None):
        super().__init__()
        self.module_name = module_name

    def filter(self, record):
        if self.module_name:
            return record.module == self.module_name
        return True
