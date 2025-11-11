from typing import Optional

from pydantic import BaseModel


class Status(BaseModel):
    ok: bool
    message: str
    version: Optional[str] = None
