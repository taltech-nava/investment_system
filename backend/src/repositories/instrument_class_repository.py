from __future__ import annotations

from sqlmodel import Session, select

from src.models.instrument_class import InstrumentClass


class InstrumentClassRepository:
    def list(self, session: Session) -> list[InstrumentClass]:
        return list(session.exec(select(InstrumentClass)).all())

    def get(self, session: Session, class_id: int) -> InstrumentClass | None:
        return session.get(InstrumentClass, class_id)


instrument_class_repository = InstrumentClassRepository()
