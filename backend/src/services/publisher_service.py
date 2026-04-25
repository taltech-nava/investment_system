from sqlmodel import Session

from src.models.publisher import Publisher
from src.repositories.publisher_repository import publisher_repository


class PublisherService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, publisher_name: str | None) -> Publisher:
        institution = publisher_name.strip() if publisher_name else ""
        if not institution:
            institution = "Self"

        publisher = publisher_repository.get_by_institution(self.session, institution)
        if not publisher:
            publisher = Publisher(institution=institution, method="manual")
            publisher = publisher_repository.create(self.session, publisher)

        return publisher
