"""Database engine and request-scoped SQLAlchemy session."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

_engine_options: dict[str, object] = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Compatibility hook; schema changes are exclusively owned by Alembic."""

    # Importing the models keeps metadata available to tests and migration
    # tooling, but application startup must never create an unstamped schema.
    from backend.persistence import models as _persistence
