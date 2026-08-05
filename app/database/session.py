import logging
from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
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
        session.execute(text("SELECT 1"))
        yield session
    except SQLAlchemyError:
        session.rollback()
        logger.exception("Database session failed during request setup or handling")
        raise
    finally:
        session.close()
