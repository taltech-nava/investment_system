import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.logging import configure_logging
from config.settings import settings
from database.engine import ping_db
from exceptions import register_exception_handlers
from routes import forecasts, ingest, instrument_classes, instruments, system

configure_logging(settings.logging.level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    ping_db()
    yield
    logger.info("App is shutting down")


app = FastAPI(
    title="Investment system",
    description="Internal API for Investment system",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(system.router, tags=["System"])
app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(forecasts.router, tags=["Forecasts"])
app.include_router(instruments.router, tags=["Instruments"])
app.include_router(instrument_classes.router, tags=["Instrument Classes"])
