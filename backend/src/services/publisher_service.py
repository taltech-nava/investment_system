from fastapi import Depends
from sqlmodel import Session

from database.session import get_session
from src.models.publisher import Publisher
from src.repositories.publisher_repository import publisher_repository


class PublisherService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Publisher]:
        return publisher_repository.list(self.session)

    def get_or_create(self, publisher_name: str | None) -> Publisher:
        institution = publisher_name.strip() if publisher_name else ""
        if not institution:
            institution = "Self"

        publisher = publisher_repository.get_by_institution(self.session, institution)
        if not publisher:
            publisher = Publisher(institution=institution, method="manual")
            publisher = publisher_repository.create(self.session, publisher)

        return publisher


def get_publisher_service(
    session: Session = Depends(get_session),
) -> PublisherService:
    return PublisherService(session)
