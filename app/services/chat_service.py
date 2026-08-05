import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.models.user import User
from app.rag.embedder import SentenceTransformerEmbedder
from app.rag.generator import OpenAITextGenerator, build_context
from app.rag.retriever import RetrievedChunk, VectorRetriever
from app.services.chat_session_service import add_message, get_or_create_session

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
) -> ChatAnswer:
    """Embed a question, retrieve owned context, and generate a grounded answer."""
    logger.info("Chat question=%r", question)
    query_embedding = embedder.embed([question])[0]
    logger.info("Generated query embedding dimension=%d", len(query_embedding))
    chunks = retriever.search(db, user.id, query_embedding, top_k)
    logger.info("Retrieved %d chunks; inspecting top 5 ranked chunks", len(chunks))
    for rank, chunk in enumerate(chunks[:5], start=1):
        logger.info(
            "Retrieved chunk rank=%d similarity=%.6f document_id=%d chunk_index=%d content=%r",
            rank,
            chunk.score,
            chunk.document_id,
            chunk.chunk_index,
            chunk.content,
        )
    context = build_context(chunks)
    logger.info("Exact context sent to LLM:\n%s", context)
    answer = generator.generate(question, context)
    return ChatAnswer(answer=answer, sources=chunks)


def answer_session_question(
    db: Session,
    user: User,
    question: str,
    session_id: int | None,
    embedder: SentenceTransformerEmbedder,
    generator: OpenAITextGenerator,
    retriever: VectorRetriever,
    top_k: int,
) -> tuple[ChatSession, ChatAnswer]:
    """Answer a question and persist both sides of the successful exchange."""
    chat_session = get_or_create_session(db, user, session_id)
    try:
        add_message(db, chat_session, "user", question)
        result = answer_question(
            db=db,
            user=user,
            question=question,
            embedder=embedder,
            generator=generator,
            retriever=retriever,
            top_k=top_k,
        )
        add_message(db, chat_session, "assistant", result.answer)
        db.commit()
        db.refresh(chat_session)
        return chat_session, result
    except Exception:
        db.rollback()
        raise
