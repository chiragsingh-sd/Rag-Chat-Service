from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.chat import ChatMessage, ChatSession
from app.models.user import User


def create_session(
    db: Session,
    user: User,
    title: str | None = None,
) -> ChatSession:
    """Create one chat session owned by the authenticated user."""
    chat_session = ChatSession(user_id=user.id, title=title)
    db.add(chat_session)
    try:
        db.commit()
        db.refresh(chat_session)
    except SQLAlchemyError:
        db.rollback()
        raise
    return chat_session


def list_sessions(db: Session, user: User) -> list[ChatSession]:
    """Return only sessions owned by the authenticated user."""
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
        ).all()
    )


def get_session(db: Session, user: User, session_id: int) -> ChatSession:
    """Load one owned session with its messages or raise HTTP 404."""
    chat_session = db.scalar(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return chat_session


def get_owned_session(db: Session, user: User, session_id: int) -> ChatSession:
    """Load one owned session without eagerly loading its message history."""
    chat_session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return chat_session


def get_or_create_session(
    db: Session,
    user: User,
    session_id: int | None,
) -> ChatSession:
    """Resolve an owned session, creating one for a first chat when omitted."""
    if session_id is None:
        chat_session = ChatSession(user_id=user.id)
        db.add(chat_session)
        db.flush()
        return chat_session
    return get_owned_session(db, user, session_id)


def load_recent_messages(
    db: Session,
    chat_session: ChatSession,
    limit: int,
) -> list[ChatMessage]:
    """Load only the latest messages for an already ownership-validated session."""
    if limit <= 0:
        return []

    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        ).all()
    )
    messages.reverse()
    return messages


def add_message(
    db: Session,
    chat_session: ChatSession,
    role: str,
    content: str,
) -> ChatMessage:
    """Stage one message in a session transaction."""
    message = ChatMessage(
        session_id=chat_session.id,
        role=role,
        content=content,
    )
    db.add(message)
    db.flush()
    return message
