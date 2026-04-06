from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.engine import ping_db
from routes import forecasts, instrument_classes, instruments, system


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

app.include_router(system.router, tags=["System"])
app.include_router(forecasts.router, tags=["Ingestion"])
app.include_router(instruments.router, tags=["Instruments"])
app.include_router(instrument_classes.router, tags=["Instrument Classes"])

