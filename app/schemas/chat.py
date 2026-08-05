from typing import Annotated

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Natural-language question submitted to the document chat endpoint."""

    question: Annotated[str, Field(min_length=1, max_length=4_000)]
    session_id: int | None = Field(default=None, gt=0)


class ChatSource(BaseModel):
    """Document location used as context for the answer."""

    document_id: int
    filename: str
    chunk_index: int


class ChatResponse(BaseModel):
    """Grounded answer and the source chunks used to produce it."""

    session_id: int
    answer: str
    sources: list[ChatSource]
