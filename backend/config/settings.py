from .database import DatabaseSettings
from .forecast_options import ForecastOptionsSettings
from .logging import LoggingSettings


class Settings:
    """
    Single entry point for all application config.
    Add new config groups here as the app grows.

    Usage anywhere in the codebase:
        from config.settings import settings
        settings.database.get_url()
        settings.database.postgres_user
        settings.logging.level
    """

    def __init__(self) -> None:
        self.database = DatabaseSettings()
        self.forecast_options = ForecastOptionsSettings()
        self.logging = LoggingSettings()


settings = Settings()
