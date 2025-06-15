from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PingResult(BaseModel):
    ok: bool = Field(..., description="True si le service est accessible")
    error: Optional[str] = Field(None, description="Message d'erreur en cas d'échec")
    detail: Optional[Dict[str, Any]] = Field(
        None, description="Données retournées par le service"
    )
    source: Optional[str] = Field(
        None, description="Nom du service pingé (github, notion...)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Date et heure de l'appel"
    )
    duration_ms: Optional[int] = Field(
        None, description="Durée de l'appel en millisecondes (optionnelle)"
    )
