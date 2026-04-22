from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from datetime import date

from src.models.price import Price


class PriceRepository:
    def save(self, session: Session, price: Price) -> Price:
        session.add(price)
        session.flush()
        return price

    def get_by_instrument_and_date(
        self, session: Session, instrument_id: int, price_date: date
    ) -> Price | None:
        return session.exec(
            select(Price).where(
                Price.instrument_id == instrument_id, Price.price_date == price_date
            )
        ).first()


price_repository = PriceRepository()
