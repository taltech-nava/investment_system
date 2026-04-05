from sqlalchemy import text
from sqlmodel import create_engine

from config.settings import settings

engine = create_engine(settings.database.get_url(), echo=True)


def ping_db() -> bool:
    """Check that the database is reachable. Returns True on success."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print("❌ Database connection failed:", e)
        return False
