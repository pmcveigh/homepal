from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def create_sqlite_engine(db_path: str) -> Engine:
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False)


def configure_session(engine):
    SessionLocal.configure(bind=engine)
    return SessionLocal


def run_integrity_check(engine: Engine) -> str:
    with engine.connect() as conn:
        return conn.execute(text("PRAGMA integrity_check")).scalar_one()
