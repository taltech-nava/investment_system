#__init__.py backend/src/services/fetcher/

from src.services.fetch_service import FetchService
from .serper_client import RawResult, SerperClient

__all__ = ["FetchService", "RawResult", "SerperClient"]