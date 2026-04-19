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
        data = source.model_dump(exclude={"id"})  # or source.dict() + pop("id")
    
        stmt = (
            insert(Source)
            .values(**data)
            .on_conflict_do_nothing(index_elements=["file_path"])
            .returning(Source)
        )
    
        result = session.execute(stmt)
        obj = result.scalar_one_or_none()
    
        session.commit()
    
        # If insert was skipped due to conflict, fetch existing row
        if obj is None:
            obj = session.execute(
                select(Source).where(Source.file_path == data["file_path"])
            ).scalar_one_or_none()
    
        return obj

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