from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ErrorCode = Literal[
    "VALIDATION_ERROR",
    "SUPABASE_NOT_CONFIGURED",
    "SUPABASE_CONNECTION_ERROR",
    "SUPABASE_DB_ERROR",
    "INTERNAL_ERROR",
]


@dataclass(frozen=True)
class AppError:
    code: ErrorCode
    message: str
    details: Any | None = None

