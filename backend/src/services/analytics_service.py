from __future__ import annotations

from statistics import mean
from typing import TYPE_CHECKING

from pydantic import BaseModel
from scipy import stats

from src.repositories.analytics_repository import analytics_repository

if TYPE_CHECKING:
    from sqlmodel import Session

BIN_LABELS = [
    -1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, -0.20, -0.10,
     0.00,  0.10,  0.20,  0.30,  0.40,  0.50,  0.60,  0.70,  0.80,  0.90,  1.00,
]
_CUTOFFS = [
    -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, -0.20, -0.10,  0.00,
     0.10,  0.20,  0.30,  0.40,  0.50,  0.60,  0.70,  0.80,  0.90,  1.00,
]


class DistributionResult(BaseModel):
    bins: list[float]
    all: list[int]
    selected: list[int]
    mean_all: float | None
    mean_selected: float | None
    significant: bool
    p_value: float | None


class ReportRowResult(BaseModel):
    report_id: int
    forecast_id: int
    review_date: str
    prediction_date: str
    ticker: str
    instrument_name: str
    publisher_id: int
    publisher_name: str | None
    forecast_price: float
    realised_price: float
    error_ratio: float
    error_percent: float
    direction_correct: bool | None
    method: str | None


class ReportsPageResult(BaseModel):
    items: list[ReportRowResult]
    page: int
    page_size: int
    total: int


def _bin(errors: list[float]) -> list[int]:
    counts = [0] * len(_CUTOFFS)
    for e in errors:
        bucket = min(sum(1 for c in _CUTOFFS if e >= c), len(_CUTOFFS) - 1)
        counts[bucket] += 1
    return counts


class AnalyticsService:
    def get_distribution(
        self,
        session: Session,
        ticker: str | None = None,
        publisher_id: int | None = None,
    ) -> DistributionResult:
        all_errors = analytics_repository.get_all_errors(session)

        if ticker is not None:
            selected_errors = analytics_repository.get_errors_by_ticker(session, ticker)
        elif publisher_id is not None:
            selected_errors = analytics_repository.get_errors_by_publisher(session, publisher_id)
        else:
            selected_errors = all_errors

        mean_all = round(mean(all_errors), 4) if all_errors else None
        mean_selected = round(mean(selected_errors), 4) if selected_errors else None

        p_value = None
        significant = False
        is_filtered = ticker is not None or publisher_id is not None
        if is_filtered and len(all_errors) >= 2 and len(selected_errors) >= 2:
            _, p = stats.ttest_ind(all_errors, selected_errors)
            p_value = round(float(p), 4)
            significant = p_value < 0.05

        return DistributionResult(
            bins=BIN_LABELS,
            all=_bin(all_errors),
            selected=_bin(selected_errors),
            mean_all=mean_all,
            mean_selected=mean_selected,
            significant=significant,
            p_value=p_value,
        )

    def get_reports(
        self,
        session: Session,
        *,
        ticker: str | None,
        publisher_id: int | None,
        page: int,
        page_size: int,
    ) -> ReportsPageResult:
        offset = (page - 1) * page_size
        rows = analytics_repository.get_report_rows(
            session,
            ticker=ticker,
            publisher_id=publisher_id,
            offset=offset,
            limit=page_size,
        )
        total = analytics_repository.get_report_rows_count(
            session,
            ticker=ticker,
            publisher_id=publisher_id,
        )

        items = [
            ReportRowResult(
                report_id=report.id,
                forecast_id=forecast.id,
                review_date=report.review_date.isoformat(),
                prediction_date=forecast.prediction_date.isoformat(),
                ticker=instrument.ticker,
                instrument_name=instrument.name,
                publisher_id=publisher.id,
                publisher_name=publisher.institution,
                forecast_price=float(forecast.predicted_price),
                realised_price=float(report.actual_price),
                error_ratio=float(report.price_return_error),
                error_percent=round(float(report.price_return_error) * 100, 2),
                direction_correct=report.direction_correct,
                method=forecast.entry_mode,
            )
            for report, forecast, instrument, publisher in rows
        ]

        return ReportsPageResult(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )


analytics_service = AnalyticsService()


def get_analytics_service() -> AnalyticsService:
    return analytics_service
