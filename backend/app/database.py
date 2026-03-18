from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,        # detect stale connections before use
    pool_recycle=300,           # recycle connections every 5 min
    pool_size=10,               # max persistent connections
    max_overflow=5,             # extra connections under load
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
