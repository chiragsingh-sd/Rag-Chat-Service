import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate

logger: logging.Logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    """Normalize an email for consistent lookup and uniqueness checks."""
    return email.strip().lower()


def register_user(db: Session, payload: UserCreate) -> User:
    """Create a user with a securely hashed password."""
    logger.info("Before email normalization")
    email: str = normalize_email(str(payload.email))
    logger.info("After email normalization")
    logger.info("Before SELECT existing user")
    try:
        existing_user: User | None = db.scalar(
            select(User).where(User.email == email)
        )
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    logger.info("After SELECT existing user")

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    logger.info("Before password hashing")
    hashed_password: str = hash_password(payload.password)
    logger.info("After password hashing")
    user: User = User(
        email=email,
        password_hash=hashed_password,
    )
    logger.info("Before db.add()")
    db.add(user)
    logger.info("After db.add()")
    logger.info("User added to session")

    try:
        logger.info("Before db.commit()")
        db.commit()
        logger.info("After db.commit()")
        logger.info("Commit successful")
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc

    logger.info("Before db.refresh()")
    db.refresh(user)
    logger.info("After db.refresh()")
    logger.info("Before returning response")
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Validate credentials without revealing which field failed."""
    normalized_email: str = normalize_email(email)
    user: User | None = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def issue_access_token(user: User) -> str:
    """Create an access token for an authenticated user."""
    return create_access_token(user.id)
