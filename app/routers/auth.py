import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserResponse
from app.schemas.errors import responses_for
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
    responses=responses_for(409, 422, 500, 503),
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Register a new user account."""
    logger.info("User registration started")
    user: User = register_user(db, payload)
    logger.info("User registration completed user_id=%d", user.id)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses=responses_for(401, 422, 500, 503),
)
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
    logger.info("User authenticated user_id=%d", user.id)
    return TokenResponse(
        access_token=issue_access_token(user),
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse, responses=responses_for(401, 500, 503))
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)
