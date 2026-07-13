"""SQLite database engine, session factory, and initialization."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

import app.core.config as _config
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_db_path() -> Path:
    url = _config.settings.database_url
    if url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", ""))
    return Path("data/ai_econometrics.db")


def get_engine():
    global _engine
    if _engine is None:
        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            _config.settings.database_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


def init_db() -> None:
    from app.storage.models import Base as _  # noqa: F401 — ensure models are registered

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    _config.settings.data_dir.mkdir(parents=True, exist_ok=True)
    _config.settings.upload_dir.mkdir(parents=True, exist_ok=True)
    _config.settings.artifact_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Database initialized at %s; upload_dir=%s, artifact_dir=%s",
        _get_db_path(),
        _config.settings.upload_dir,
        _config.settings.artifact_dir,
    )


def reset_engine() -> None:
    """Tear down engine and session factory — used by tests."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
