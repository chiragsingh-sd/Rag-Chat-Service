from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    """Optional metadata for a newly created chat session."""

    title: Annotated[str | None, Field(default=None, max_length=200)] = None


class ChatSessionResponse(BaseModel):
    """Summary returned when creating or listing chat sessions."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    created_at: datetime


class ChatMessageResponse(BaseModel):
    """One persisted user or assistant message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatSessionDetailResponse(ChatSessionResponse):
    """A session and its messages in chronological order."""

    messages: list[ChatMessageResponse]
