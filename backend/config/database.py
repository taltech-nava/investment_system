from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve to the project root .env (investment_system/.env), two levels above backend/config/
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str
    db_port: int = 5432

    def get_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.db_host}:"
            f"{self.db_port}/{self.postgres_db}"
        )
