#publisher_repository.py backend/src/repositories/

#New file. create() and get_by_url() used when saving each search result

from __future__ import annotations

from sqlmodel import Session, select

from src.models.publisher import Publisher


class PublisherRepository:
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