from .database import DatabaseSettings
from .forecast_options import ForecastOptionsSettings
from .llm import LLMSettings
from .logging import LoggingSettings


class Settings:
    """
    Single entry point for all application config.
    Add new config groups here as the app grows.

    Usage anywhere in the codebase:
        from config.settings import settings
        settings.database.get_url()
        settings.logging.level
        settings.llm.llm_provider
    """

    def __init__(self) -> None:
        self.database = DatabaseSettings()
        self.forecast_options = ForecastOptionsSettings()
        self.logging = LoggingSettings()
        self.llm = LLMSettings()


settings = Settings()
