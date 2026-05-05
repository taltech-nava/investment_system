from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from src.models.report import Report

if TYPE_CHECKING:
    from sqlmodel import Session
from src.repositories.report_repository import report_repository
from src.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, session: Session, yfinance: YFinanceService | None = None) -> None:
        self.session = session
        self.yfinance = yfinance or YFinanceService()

    def generate_reports(self) -> int:
        today = date.today()
        forecasts = report_repository.get_forecasts_without_reports(self.session, today)
        written = 0

        for forecast in forecasts:
            ticker = forecast.instrument.ticker
            actual_price = self.yfinance.fetch_realised_price(ticker, forecast.maturation_date)
            if actual_price is None:
                logger.info("No price for %s on %s — skipping", ticker, forecast.maturation_date)
                continue

            actual = Decimal(str(actual_price))
            predicted = forecast.predicted_price
            price_return_error = (predicted - actual) / actual

            direction_correct: bool | None = None
            if forecast.spot_price_at_prediction is not None:
                spot = forecast.spot_price_at_prediction
                direction_correct = (predicted > spot) == (actual > spot)

            report = Report(
                forecast_id=forecast.id,
                review_date=today,
                actual_price=actual,
                price_return_error=price_return_error,
                direction_correct=direction_correct,
            )
            report_repository.create(self.session, report)
            written += 1
            logger.info("Report written for forecast %d (%s)", forecast.id, ticker)

        logger.info("generate_reports complete: %d reports written", written)
        return written
