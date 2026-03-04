from __future__ import annotations

import re

from app.core.config import settings


PROMPT_INJECTION_PATTERNS: tuple[str, ...] = (
    r"ignore\s+previous\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"developer\s+message",
    r"tool\s+instructions",
    r"bypass\s+security",
    r"exfiltrat",
    r"read\s+file",
    r"shell\s+command",
)


def sanitize_user_text(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) > settings.PROMPT_GUARD_MAX_QUERY_CHARS:
        cleaned = cleaned[: settings.PROMPT_GUARD_MAX_QUERY_CHARS]
    return cleaned


def detect_prompt_injection_attempt(value: str) -> bool:
    lowered = value.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False

