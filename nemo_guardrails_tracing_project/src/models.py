from dataclasses import dataclass
from typing import Any
@dataclass
class RailResult:
    allowed: bool
    reason: str
    sanitized_text: str | None = None
    code: str | None = None
    mechanism: str | None = None
    data: dict[str, Any] | None = None
