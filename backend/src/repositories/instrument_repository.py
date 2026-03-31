from __future__ import annotations

from sqlmodel import Session, select

from src.models.instrument import Instrument


class InstrumentRepository:
    def list(self, session: Session) -> list[Instrument]:
        return list(session.exec(select(Instrument)).all())

    def list_by_class(self, session: Session, class_id: int) -> list[Instrument]:
        return list(session.exec(select(Instrument).where(Instrument.class_id == class_id)).all())

    def get(self, session: Session, instrument_id: int) -> Instrument | None:
        return session.get(Instrument, instrument_id)

    def get_by_ticker(self, session: Session, ticker: str) -> Instrument | None:
        return session.exec(select(Instrument).where(Instrument.ticker == ticker)).first()

    def delete(self, session: Session, instrument_id: int) -> bool:
        instrument = session.get(Instrument, instrument_id)
        if not instrument:
            return False
        session.delete(instrument)
        session.commit()
        return True


instrument_repository = InstrumentRepository()
