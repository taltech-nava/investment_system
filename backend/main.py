import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from sqlmodel import Session

from config.logging import configure_logging
from config.settings import settings
import logging
from database.engine import engine, ping_db
from exceptions import register_exception_handlers
from routes import (
    analytics,
    forecasts,
    ingest,
    instrument_classes,
    instruments,
    publishers,
    system,
    fetch,
)
from src.services.report_service import ReportService

configure_logging(settings.logging.level)

logger = logging.getLogger(__name__)


def _run_generate_reports() -> None:
    with Session(engine) as session:
        written = ReportService(session).generate_reports()
    logger.info("Scheduled report run complete: %d written", written)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    ping_db()

    scheduler = AsyncIOScheduler()
    # Runs daily at 21:00 UTC (after US market close at ~21:00 UTC / 16:00 ET)
    scheduler.add_job(_run_generate_reports, CronTrigger(hour=21, minute=0))
    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown()
    logger.info("App is shutting down")


app = FastAPI(
    title="Investment system",
    description="Internal API for Investment system",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(analytics.router, tags=["Analytics"])
app.include_router(system.router, tags=["System"])
app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(forecasts.router, tags=["Forecasts"])
app.include_router(instruments.router, tags=["Instruments"])
app.include_router(instrument_classes.router, tags=["Instrument Classes"])
app.include_router(fetch.router, tags=["Fetch"])
app.include_router(publishers.router, tags=["Publishers"])

