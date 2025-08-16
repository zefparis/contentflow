from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use DATABASE_URL from settings (uppercase field in Settings)
DATABASE_URL = getattr(settings, "DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL.lower() else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Create all tables based on models metadata."""
    # Import models to register metadata, then create all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
