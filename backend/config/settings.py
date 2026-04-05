from .database import DatabaseSettings


class Settings:
    """
    Single entry point for all application config.
    Add new config groups here as the app grows.

    Usage anywhere in the codebase:
        from config.settings import settings
        settings.database.get_url()
        settings.database.postgres_user
    """

    def __init__(self) -> None:
        self.database = DatabaseSettings()


settings = Settings()
