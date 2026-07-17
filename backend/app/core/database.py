from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

Base = declarative_base()

class DatabaseManager:
    """Manages the SQLAlchemy engine and session factory.
    Allows swapping the engine for testing purposes.
    """
    def __init__(self, db_url: str | None = None):
        self.db_url = settings.DATABASE_URL if db_url is None else db_url
        engine_options = {}
        if self.db_url.startswith("sqlite"):
            engine_options["connect_args"] = {"check_same_thread": False}

        # Do not catch engine or connection errors here. The configured database
        # must remain the source of truth; falling back to SQLite would hide
        # production outages and could write data to the wrong store.
        self._engine = create_engine(self.db_url, **engine_options)
        self._session_factory = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self._engine
        )

    @property
    def engine(self):
        return self._engine

    def get_session(self):
        return self._session_factory()

# Global instance for the application
db_manager = DatabaseManager()

def get_db():
    """Dependency for FastAPI endpoints to get a DB session."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
