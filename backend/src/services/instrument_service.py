from fastapi import Depends
from sqlmodel import Session

from database.session import get_session
from src.models.instrument import Instrument
from src.repositories.instrument_repository import instrument_repository


class InstrumentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Instrument]:
        return instrument_repository.list(self.session)

    def get(self, instrument_id: int) -> Instrument | None:
        return instrument_repository.get(self.session, instrument_id)

    def delete(self, instrument_id: int) -> bool:
        return instrument_repository.delete(self.session, instrument_id)


def get_instrument_service(
    session: Session = Depends(get_session),
) -> InstrumentService:
    return InstrumentService(session)
