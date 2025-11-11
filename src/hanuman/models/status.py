from pydantic import BaseModel
from typing import Optional

class Status(BaseModel):
    ok: bool
    message: str
    version: Optional[str] = None
