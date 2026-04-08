#source_repository.py backend/src/repositories/
#Add create(), get(), list() methods alongside your existing audit methods

from __future__ import annotations

from sqlmodel import Session, select

from src.models.source import Source


class SourceRepository:

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Session, source: Source) -> Source:
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

    def update_status(
        self,
        session: Session,
        source_id: int,
        status: str,
        reason: str | None = None,
    ) -> None:
        source = session.get(Source, source_id)
        if source is None:
            return
        source.audit_status = status
        source.rejection_reason = reason[:20] if reason else None
        session.add(source)


source_repository = SourceRepository()