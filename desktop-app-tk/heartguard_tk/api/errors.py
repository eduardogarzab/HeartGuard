"""Domain specific exceptions for HeartGuard API interactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class ApiError(Exception):
    """Represents an HTTP error coming from the HeartGuard gateway."""

    message: str
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    payload: Optional[Any] = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        parts: list[str] = [self.message]
        if self.status_code is not None:
            parts.append(f"(status={self.status_code})")
        if self.error_code:
            parts.append(f"code={self.error_code}")
        return " ".join(parts)
