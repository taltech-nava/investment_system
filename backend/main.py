from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.engine import ping_db
import logging
from exceptions import register_exception_handlers
from routes import publishers, forecasts, fetch, instrument_classes, instruments, system

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    ping_db()
    yield
    print("App is shutting down")

app = FastAPI(
    title="Investment system",
    description="Internal API for Investment system",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(system.router, tags=["System"])
app.include_router(instruments.router, tags=["Instruments"])
app.include_router(instrument_classes.router, tags=["Instrument Classes"])
app.include_router(fetch.router, tags=["Fetch"])
app.include_router(forecasts.router, tags=["Forecasts"])
app.include_router(publishers.router, tags=["Publishers"])
