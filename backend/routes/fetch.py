from fastapi import APIRouter
from config.fetcher import FetcherSettings
from database.session import get_session
from src.ingestion.serper_client import SerperClient
from src.ingestion.fetch_service import FetchService
from sqlmodel import select
from src.models.source import Source
from sqlalchemy import text
import json


router = APIRouter()

@router.get("/fetch/{ticker}")
def fetch_ticker(ticker: str):
    cfg = FetcherSettings()

    serper = SerperClient(
        api_key=cfg.serper_api_key,
        max_results=cfg.serper_max_results,
        period=cfg.serper_period,
    )

    session_gen = get_session()
    session = next(session_gen)

    try:
        service = FetchService(
            session=session,
            serper_client=serper,
            query_template=cfg.query_template
        )

        n = service.fetch_ticker(ticker.upper())

        return {"status": "ok", "saved": n}

    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass
        
        
@router.get("/sources")
def get_sources():
    session_gen = get_session()
    session = next(session_gen)

    try:
        results = session.exec(select(Source)).all()
        return results

    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass