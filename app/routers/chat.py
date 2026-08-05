from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.rag.embedder import get_embedder
from app.rag.generator import get_generator
from app.rag.retriever import VectorRetriever
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.schemas.chat_sessions import (
    ChatSessionCreate,
    ChatSessionDetailResponse,
    ChatSessionResponse,
)
from app.services.chat_service import answer_session_question
from app.services.chat_session_service import create_session, get_session, list_sessions

router: APIRouter = APIRouter(prefix="/chat", tags=["chat"])
retriever = VectorRetriever()


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: ChatSessionCreate | None = None,
) -> ChatSessionResponse:
    """Create one authenticated user's empty chat session."""
    session = create_session(db, current_user, payload.title if payload else None)
    return ChatSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_chat_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ChatSessionResponse]:
    """List the authenticated user's chat sessions."""
    return [
        ChatSessionResponse.model_validate(session)
        for session in list_sessions(db, current_user)
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_chat_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatSessionDetailResponse:
    """Return one owned chat session and its messages."""
    session = get_session(db, current_user, session_id)
    return ChatSessionDetailResponse.model_validate(session)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    """Answer one authenticated question using the user's stored document chunks."""
    settings = get_settings()
    session, result = answer_session_question(
        db=db,
        user=current_user,
        question=payload.question,
        session_id=payload.session_id,
        embedder=get_embedder(),
        generator=get_generator(),
        retriever=retriever,
        top_k=settings.rag_top_k,
    )
    return ChatResponse(
        session_id=session.id,
        answer=result.answer,
        sources=[
            ChatSource(
                document_id=source.document_id,
                filename=source.filename,
                chunk_index=source.chunk_index,
            )
            for source in result.sources
        ],
    )
