import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.models.user import User
from app.rag.embedder import SentenceTransformerEmbedder, get_embedder
from app.rag.generator import (
    OpenAITextGenerator,
    build_context,
    build_conversation_history,
    get_generator,
)
from app.rag.retriever import RetrievedChunk, VectorRetriever
from app.services.chat_session_service import (
    add_message,
    get_or_create_session,
    load_recent_messages,
)

logger: logging.Logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatAnswer:
    """Internal result returned by the chat use case."""

    answer: str
    sources: list[RetrievedChunk]


def answer_question(
    db: Session,
    user: User,
    question: str,
    embedder: SentenceTransformerEmbedder,
    generator: OpenAITextGenerator,
    retriever: VectorRetriever,
    top_k: int,
    conversation_history: str = "",
) -> ChatAnswer:
    """Embed a question, retrieve owned context, and generate a grounded answer."""
    query_embedding = embedder.embed([question])[0]
    logger.info("Generated query embedding dimension=%d", len(query_embedding))
    chunks = retriever.search(db, user.id, query_embedding, top_k)
    logger.info("Retrieved %d chunks", len(chunks))
    context = build_context(chunks)
    answer = generator.generate(question, context, conversation_history)
    return ChatAnswer(answer=answer, sources=chunks)


def answer_session_question(
    db: Session,
    user: User,
    question: str,
    session_id: int | None,
    embedder: SentenceTransformerEmbedder | None,
    generator: OpenAITextGenerator | None,
    retriever: VectorRetriever,
    top_k: int,
    history_limit: int = 10,
) -> tuple[ChatSession, ChatAnswer]:
    """Answer a question and persist both sides of the successful exchange."""
    chat_session = get_or_create_session(db, user, session_id)
    logger.info("Chat request started session_id=%d", chat_session.id)
    try:
        history_messages = load_recent_messages(db, chat_session, history_limit)
        logger.info(
            "Loaded %d history messages for session id=%d",
            len(history_messages),
            chat_session.id,
        )
        conversation_history = build_conversation_history(history_messages)
        embedder = embedder or get_embedder()
        generator = generator or get_generator()
        add_message(db, chat_session, "user", question)
        result = answer_question(
            db=db,
            user=user,
            question=question,
            embedder=embedder,
            generator=generator,
            retriever=retriever,
            top_k=top_k,
            conversation_history=conversation_history,
        )
        add_message(db, chat_session, "assistant", result.answer)
        db.commit()
        db.refresh(chat_session)
        logger.info("Chat response stored session_id=%d", chat_session.id)
        return chat_session, result
    except Exception:
        db.rollback()
        raise
