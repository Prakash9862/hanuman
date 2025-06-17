from typing import Dict, Optional

from pydantic import BaseModel


class StatusResult(BaseModel):
    status: str
    version: str
    token_previews: Optional[Dict[str, str]] = None
