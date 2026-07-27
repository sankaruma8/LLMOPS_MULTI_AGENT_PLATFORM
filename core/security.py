import re
import hashlib
import secrets
from typing import Any, Dict, Optional, List
from datetime import datetime
import html


class InputSanitizer:

    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"eval\s*\(",
        r"exec\s*\(",
        r"__\w+__",
        r"\b(drop|truncate|delete|insert|update)\s+(table|from|into)",
    ]

    SQL_INJECTION_PATTERNS = [
        r"union\s+select",
        r"or\s+1\s*=\s*1",
        r";\s*(drop|delete|update|insert)",
        r"--\s*$",
        r"/\*.*?\*/",
    ]

    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 10000) -> str:

        if not text:
            return ""

        text = text[:max_length]

        text = html.escape(text)

        for pattern in cls.DANGEROUS_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:

        if not filename:
            return "unnamed"

        filename = re.sub(r'[^\w\-.]', '_', filename)

        filename = re.sub(r'_+', '_', filename)

        filename = filename.strip('_.')

        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255 - len(ext) - 1] + '.' + ext if ext else name[:255]

        dangerous_names = [
            'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3',
            'lpt1', 'lpt2', 'lpt3', 'core'
        ]

        if filename.lower().split('.')[0] in dangerous_names:
            filename = f"safe_{filename}"

        return filename

    @classmethod
    def check_sql_injection(cls, text: str) -> bool:

        text_lower = text.lower()

        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    @classmethod
    def validate_session_id(cls, session_id: str) -> bool:

        if not session_id:
            return False

        if len(session_id) > 100:
            return False

        return bool(re.match(r'^[\w\-]+$', session_id))


class EncryptionManager:

    def __init__(self, secret_key: str = None):

        self._secret_key = secret_key or secrets.token_hex(32)

    def hash_data(self, data: str) -> str:

        return hashlib.sha256(
            f"{self._secret_key}:{data}".encode()
        ).hexdigest()

    def verify_hash(self, data: str, hash_value: str) -> bool:

        return self.hash_data(data) == hash_value

    def generate_token(self, length: int = 32) -> str:

        return secrets.token_urlsafe(length)

    def mask_sensitive(self, data: str, visible_chars: int = 4) -> str:

        if len(data) <= visible_chars:
            return "*" * len(data)

        return data[:visible_chars] + "*" * (len(data) - visible_chars)


class AuditLogger:

    def __init__(self, max_entries: int = 10000):

        self._entries: List[Dict] = []
        self._max_entries = max_entries

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ):

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "details": details or {},
            "ip_address": ip_address
        }

        self._entries.append(entry)

        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def get_entries(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:

        entries = self._entries

        if user_id:
            entries = [e for e in entries if e["user_id"] == user_id]

        if action:
            entries = [e for e in entries if e["action"] == action]

        return entries[-limit:]

    def get_stats(self) -> Dict:

        action_counts = {}
        for entry in self._entries:
            action = entry["action"]
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "total_entries": len(self._entries),
            "action_distribution": action_counts
        }


class SecurityMiddleware:

    def __init__(self):

        self.sanitizer = InputSanitizer()
        self.encryption = EncryptionManager()
        self.audit = AuditLogger()

    def validate_request(self, request_data: Dict) -> Dict:

        errors = []

        for key, value in request_data.items():
            if isinstance(value, str):
                if self.sanitizer.check_sql_injection(value):
                    errors.append(f"Potential SQL injection in field: {key}")

                if len(value) > 50000:
                    errors.append(f"Field {key} exceeds maximum length")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def sanitize_request(self, request_data: Dict) -> Dict:

        sanitized = {}

        for key, value in request_data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitizer.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_request(value)
            else:
                sanitized[key] = value

        return sanitized

    def log_security_event(
        self,
        event_type: str,
        details: Dict,
        ip_address: Optional[str] = None
    ):

        self.audit.log(
            action=f"security:{event_type}",
            details=details,
            ip_address=ip_address
        )


sanitizer = InputSanitizer()
encryption = EncryptionManager()
security_middleware = SecurityMiddleware()
audit_logger = AuditLogger()
