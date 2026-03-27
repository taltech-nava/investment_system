from fastapi import FastAPI

from routes import system

app = FastAPI(
    title="Investment system",
    description="Internal API for Investment system",
    version="1.0.0",
)

app.include_router(system.router, tags=["System"])
