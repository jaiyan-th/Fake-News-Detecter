"""
Database Engine & Session Management using SQLAlchemy
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.core.config import settings

# Ensure the database directory exists
db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database")
os.makedirs(db_dir, exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{os.path.join(db_dir, 'news_verification.db').replace(os.sep, '/')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db_session():
    """Dependency generator for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables on startup"""
    import backend.db.models  # Ensure models are imported
    Base.metadata.create_all(bind=engine)

# Auto-initialize tables
init_db()

