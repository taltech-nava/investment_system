from __future__ import annotations
from sqlmodel import select
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlmodel import Session
from src.models.publisher import Publisher


class PublisherRepository:
    def get_by_institution(self, session: Session, institution: str) -> Publisher | None:
        return session.exec(select(Publisher).where(Publisher.institution == institution)).first()

    def create(self, session: Session, publisher: Publisher) -> Publisher:
        session.add(publisher)
        session.commit()
        session.refresh(publisher)
        return publisher

    def get(self, session: Session, publisher_id: int) -> Publisher | None:
        return session.get(Publisher, publisher_id)

    def get_by_url(self, session: Session, url: str) -> Publisher | None:
        return session.exec(select(Publisher).where(Publisher.url == url)).first()

    def list(self, session: Session) -> list[Publisher]:
        return list(session.exec(select(Publisher)).all())

publisher_repository = PublisherRepository()
