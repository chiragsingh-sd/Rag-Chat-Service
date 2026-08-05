import math
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk


@dataclass(frozen=True)
class RetrievedChunk:
    """A document chunk ranked by cosine similarity to a question."""

    document_id: int
    filename: str
    chunk_index: int
    content: str
    score: float


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Calculate cosine similarity for two equal-length embedding vectors."""
    if len(left) != len(right):
        raise ValueError("Embedding dimensions do not match")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


class VectorRetriever:
    """Search stored embeddings within the authenticated user's documents."""

    def search(
        self,
        db: Session,
        user_id: int,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Load owned chunks, rank them by cosine similarity, and return top-k."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        rows = db.execute(
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.user_id == user_id)
        ).all()

        ranked = [
            RetrievedChunk(
                document_id=chunk.document_id,
                filename=filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=_cosine_similarity(query_embedding, chunk.embedding),
            )
            for chunk, filename in rows
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]
