from typing import Optional

from pydantic import BaseModel


class StatusResult(BaseModel):
    status: str
    version: str
    notion_token_preview: Optional[str] = None
