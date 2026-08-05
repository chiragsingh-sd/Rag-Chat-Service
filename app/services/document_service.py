import logging
import re
import unicodedata
from typing import BinaryIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.rag.chunker import TextChunker
from app.rag.embedder import SentenceTransformerEmbedder, get_embedder

logger: logging.Logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Normalize Unicode, line endings, and redundant whitespace."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _file_size(file: BinaryIO) -> int:
    """Return the number of bytes read from an in-memory upload."""
    return file.tell()


def ingest_document(
    db: Session,
    user: User,
    upload: UploadFile,
    embedder: SentenceTransformerEmbedder | None,
    chunker: TextChunker | None = None,
) -> Document:
    """Validate, process, embed, and persist one text document transactionally."""
    try:
        return _ingest_document(db, user, upload, embedder, chunker)
    except HTTPException as exc:
        logger.warning(
            "Upload rejected filename=%r status_code=%d",
            upload.filename,
            exc.status_code,
        )
        raise
    except Exception:
        logger.exception("Document ingestion failed for filename=%r", upload.filename)
        raise


def _ingest_document(
    db: Session,
    user: User,
    upload: UploadFile,
    embedder: SentenceTransformerEmbedder,
    chunker: TextChunker | None = None,
) -> Document:
    """Perform document ingestion without changing the public service boundary."""
    filename = upload.filename or ""
    if not filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .txt files are supported",
        )

    raw_content = upload.file.read()
    try:
        source_text = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded .txt file must be UTF-8 encoded",
        ) from exc

    normalized_text = normalize_text(source_text)
    if not normalized_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded document is empty",
        )

    text_chunker = chunker or TextChunker()
    chunks = text_chunker.chunk(normalized_text)
    logger.info("Generated %d chunks filename=%r", len(chunks), filename)
    active_embedder = embedder or get_embedder()
    embeddings = active_embedder.embed([chunk.content for chunk in chunks])
    logger.info("Generated embeddings filename=%r count=%d", filename, len(embeddings))
    if len(chunks) != len(embeddings):
        raise RuntimeError("Embedding count does not match chunk count")

    try:
        document = Document(
            user_id=user.id,
            filename=filename,
            content_type=upload.content_type or "text/plain",
            file_size=_file_size(upload.file),
        )
        db.add(document)
        db.flush()

        db.add_all(
            [
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]
        )
        db.commit()
        db.refresh(document)
    except SQLAlchemyError:
        db.rollback()
        raise
    return document
