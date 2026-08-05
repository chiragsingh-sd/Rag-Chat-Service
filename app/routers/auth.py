import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserResponse
from app.services.auth_service import (
    authenticate_user,
    issue_access_token,
    register_user,
)

router: APIRouter = APIRouter(prefix="/api/auth", tags=["auth"])
logger: logging.Logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Register a new user account."""
    logger.info("Before entering register endpoint")
    logger.info("Reached register endpoint")
    logger.info("After entering register endpoint")
    logger.info("User validated")
    logger.info("Before register service")
    user: User = register_user(db, payload)
    logger.info("After register service")
    response: UserResponse = UserResponse.model_validate(user)
    logger.info("Before returning response")
    logger.info("Returning response")
    return response


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate a user and return a bearer access token."""
    user: User = authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    return TokenResponse(
        access_token=issue_access_token(user),
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)
