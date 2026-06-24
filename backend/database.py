"""数据库初始化"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "game.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.models import save as _save
    from backend.models import user as _user
    from backend.models import token as _token
    Base.metadata.create_all(bind=engine)

    # SQLite迁移：给save_slots加user_id列（如果缺失）
    import sqlalchemy
    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(sqlalchemy.text("PRAGMA table_info(save_slots)")).fetchall()]
        if 'user_id' not in cols:
            conn.execute(sqlalchemy.text("ALTER TABLE save_slots ADD COLUMN user_id INTEGER DEFAULT 0"))
            conn.commit()
