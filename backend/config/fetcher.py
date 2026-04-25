#fetcher.py backend/config/

#Loads SERPER_API_KEY, max results, period, and query template from .env

"""Fetcher configuration loaded from .env via pydantic-settings.

Add to your .env:
    SERPER_API_KEY=your_key
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class FetcherSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    serper_api_key: str = ""

    # How many search results to request per ticker
    serper_max_results: int = 10

    # Serper time-bound filter — "qdr:w" = last week, "qdr:m" = last month, etc.
    serper_period: str = "qdr:m"

    # Query template. {ticker} is substituted at runtime.
    query_template: str = '{ticker} stock "price target" (raises OR raised OR upgrade OR downgrade OR outlook)'