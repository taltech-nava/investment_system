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


analytics_service = AnalyticsService()


def get_analytics_service() -> AnalyticsService:
    return analytics_service
