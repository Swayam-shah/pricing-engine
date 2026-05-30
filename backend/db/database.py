from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
from config import settings

# Create the database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # test connection before using it
    pool_size=5,             # max 5 connections in pool
    max_overflow=10          # allow 10 extra connections under load
)

# Each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Creates all tables in the database if they don't exist.
    Call this once when the app starts.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def get_db():
    """
    FastAPI dependency — gives each request a DB session,
    and closes it cleanly when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()