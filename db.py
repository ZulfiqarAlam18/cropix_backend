# db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL - default to PostgreSQL, fallback to SQLite for development
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/cropix")

# Handle SQLite fallback for local development
if "sqlite" in DB_URL.lower():
    engine = create_engine(DB_URL, future=True, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_URL, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database initialization function
def init_db():
    """Initialize database tables"""
    # Import models to ensure they're registered
    from community.models import Post, Comment, Like
    Base.metadata.create_all(bind=engine)
