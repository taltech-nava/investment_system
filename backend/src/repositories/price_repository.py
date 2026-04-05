from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from src.models.price import Price


class PriceRepository:
    def save(self, session: Session, price: Price) -> Price:
        session.add(price)
        session.commit()
        session.refresh(price)
        return price

    def get_by_instrument_and_date(self, session: Session, instrument_id: int, price_date: date) -> Price | None:
        return session.exec(
            select(Price).where(Price.instrument_id == instrument_id, Price.price_date == price_date)
        ).first()


price_repository = PriceRepository()
