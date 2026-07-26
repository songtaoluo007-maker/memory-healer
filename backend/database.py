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
    # Local development may bootstrap an empty SQLite database directly. All
    # deployed environments use Alembic migrations.
    if settings.is_production:
        return
    from backend.persistence import models as _persistence

    Base.metadata.create_all(bind=engine)
