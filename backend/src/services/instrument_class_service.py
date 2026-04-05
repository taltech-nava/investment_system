from fastapi import Depends
from sqlmodel import Session

from database.session import get_session
from src.models.instrument_class import InstrumentClass
from src.repositories.instrument_class_repository import instrument_class_repository


class InstrumentClassService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[InstrumentClass]:
        return instrument_class_repository.list(self.session)

    def get(self, class_id: int) -> InstrumentClass | None:
        return instrument_class_repository.get(self.session, class_id)


def get_instrument_class_service(
    session: Session = Depends(get_session),
) -> InstrumentClassService:
    return InstrumentClassService(session)
