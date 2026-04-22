#source_repository.py backend/src/repositories/
#Add create(), get(), list() methods alongside your existing audit methods

from __future__ import annotations

from sqlmodel import Session, select

from src.models.source import Source

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select


class SourceRepository:

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Session, source: Source) -> Source:
        # Check for existing row by file_path (duplicate guard)
        if source.file_path:
            existing = session.execute(
                select(Source).where(Source.file_path == source.file_path)
            ).scalar_one_or_none()
            if existing:
                return existing

        session.add(source)
        session.commit()
        session.refresh(source)
        return source

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Session, source_id: int) -> Source | None:
        return session.get(Source, source_id)

    def get_pending_sources(self, session: Session, ticker: str) -> list[Source]:
        """
        Fetch Serper sources that have not been audited yet.
        Ticker matching via search_subjects is left to the caller until
        the JSON structure is confirmed stable.
        """
        results = session.exec(
            select(Source).where(
                Source.search_engine == "serper",       # type: ignore[union-attr]
                Source.audit_status.is_(None),          # type: ignore[union-attr]
            )
        ).all()
        return list(results)

    def list(self, session: Session) -> list[Source]:
        return list(session.exec(select(Source)).all())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, session: Session, source_id: int, **kwargs) -> Source | None:
        source = session.get(Source, source_id)
        if source is None:
            return None
        for key, value in kwargs.items():
            setattr(source, key, value)
        session.add(source)
        session.commit()
        return source


source_repository = SourceRepository()