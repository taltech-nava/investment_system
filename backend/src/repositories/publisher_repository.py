from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import select

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

    def get_or_create(self, session: Session, institution: str) -> Publisher:
        publisher = self.get_by_institution(session, institution)
        if publisher:
            return publisher

        publisher = Publisher(institution=institution)
        return self.create(session, publisher)


publisher_repository = PublisherRepository()
