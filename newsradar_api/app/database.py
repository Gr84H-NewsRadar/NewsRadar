from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Motor de BD con soporte para SQLite y PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Generador de sesiones de BD para inyección de dependencias en FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
