"""Database connection and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/mandala"  # Default for local dev
)

# Convert postgresql:// to postgresql+psycopg:// to use psycopg3
# SQLAlchemy needs the explicit dialect specification
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Create engine with psycopg3 driver
# Add connection pooling and retry settings for Neon/cloud databases
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Additional connections if pool is exhausted
    pool_pre_ping=True,  # Verify connections before using (handles dropped connections)
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "connect_timeout": 10,  # 10 second connection timeout
        "sslmode": "require",  # Require SSL for Neon
    },
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
