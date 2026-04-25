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


publisher_repository = PublisherRepository()
