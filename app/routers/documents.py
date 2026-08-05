import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.documents import DocumentUploadResponse
from app.schemas.errors import responses_for
from app.services.document_service import ingest_document

router: APIRouter = APIRouter(prefix="/documents", tags=["documents"])
logger: logging.Logger = logging.getLogger(__name__)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses=responses_for(401, 415, 422, 500, 503),
)
def upload_document(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentUploadResponse:
    """Synchronously ingest one authenticated UTF-8 text document."""
    logger.info("Upload started user_id=%d filename=%r", current_user.id, file.filename)
    document = ingest_document(
        db=db,
        user=current_user,
        upload=file,
        embedder=None,
    )
    response = DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        chunk_count=len(document.chunks),
        created_at=document.created_at,
    )
    logger.info("Upload completed user_id=%d document_id=%d", current_user.id, document.id)
    return response
