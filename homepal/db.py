from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass



def create_sqlite_engine(db_path: str):
    return create_engine(f"sqlite+pysqlite:///{db_path}", future=True)


SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False)



def configure_session(engine):
    SessionLocal.configure(bind=engine)
    return SessionLocal
