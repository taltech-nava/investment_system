from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from datetime import date

from src.models.forecast import Forecast
from src.models.report import Report


class ReportRepository:
    def get_forecasts_without_reports(self, session: Session, as_of_date: date) -> list[Forecast]:
        reported_ids = select(Report.forecast_id)
        return list(
            session.exec(
                select(Forecast).where(
                    Forecast.maturation_date <= as_of_date,
                    Forecast.predicted_price.is_not(None),
                    Forecast.id.not_in(reported_ids),
                )
            ).all()
        )

    def create(self, session: Session, report: Report) -> Report:
        session.add(report)
        session.commit()
        session.refresh(report)
        return report


report_repository = ReportRepository()
