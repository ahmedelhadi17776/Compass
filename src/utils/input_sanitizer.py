import re
import html
from typing import Any


class InputSanitizer:
    @staticmethod
    def sanitize_string(input_str: str) -> str:
        # HTML escape
        escaped = html.escape(input_str)
        # Remove potential SQL injection patterns
        cleaned = re.sub(r'[\'\";]', '', escaped)
        return cleaned

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
