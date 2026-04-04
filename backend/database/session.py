from collections.abc import Generator

from sqlmodel import Session

from .engine import engine


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request."""
    with Session(engine) as session:
        yield session
