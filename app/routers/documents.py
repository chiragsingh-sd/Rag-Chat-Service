import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.rag.embedder import get_embedder
from app.schemas.documents import DocumentUploadResponse
from app.services.document_service import ingest_document

router: APIRouter = APIRouter(prefix="/documents", tags=["documents"])
logger: logging.Logger = logging.getLogger(__name__)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentUploadResponse:
    """Synchronously ingest one authenticated UTF-8 text document."""
    try:
        document = ingest_document(
            db=db,
            user=current_user,
            upload=file,
            embedder=get_embedder(),
        )
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            file_size=document.file_size,
            chunk_count=len(document.chunks),
            created_at=document.created_at,
        )
    except Exception:
        logger.exception("Document upload failed for filename=%r", file.filename)
        raise
