from __future__ import annotations

from pydantic import BaseModel, Field


class GmailStatus(BaseModel):
    configured: bool
    connected: bool
    email: str | None = None
    unread: int = 0
    message: str | None = None


class GmailMessageSummary(BaseModel):
    id: str
    thread_id: str
    subject: str = "(Sans objet)"
    sender: str = "Inconnu"
    date: str | None = None
    snippet: str = ""
    unread: bool = False
    important: bool = False
    labels: list[str] = Field(default_factory=list)


class GmailMessageList(BaseModel):
    messages: list[GmailMessageSummary]
    total: int
    next_page_token: str | None = None


class GmailMessageDetail(GmailMessageSummary):
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    body: str = ""
