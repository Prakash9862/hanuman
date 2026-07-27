from datetime import UTC, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PingResult(BaseModel):
    ok: bool = Field(..., description="True si le service est accessible")
    error: Optional[str] = None  # ✅ changement ici
    detail: Optional[Dict[str, Any]] = None  # ✅
    source: Optional[str] = None  # ✅
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Date et heure de l'appel"
    )
    duration_ms: Optional[int] = None  # ✅
