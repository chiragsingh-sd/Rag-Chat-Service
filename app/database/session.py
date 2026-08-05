import logging
from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import engine

logger: logging.Logger = logging.getLogger(__name__)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session per request."""
    session: Session = SessionLocal()
    try:
        logger.info("Before database SELECT 1 connectivity check")
        session.execute(text("SELECT 1"))
        logger.info("Database SELECT 1 connectivity check succeeded")
        yield session
    finally:
        session.close()
