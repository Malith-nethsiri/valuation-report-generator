from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Validate DATABASE_URL exists
if not DATABASE_URL:
    logger.critical("DATABASE_URL environment variable is not set")
    raise RuntimeError("DATABASE_URL environment variable is required")

# Create SQLAlchemy engine with enhanced connection pooling and error handling.
# Connection health check is performed in startup_event (main.py), not here,
# so that importing this module does not require a live database connection.
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,          # Test connections before using
        pool_size=10,                # Connection pool size
        max_overflow=20,             # Max connections beyond pool_size
        pool_recycle=3600,           # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,   # 10 second timeout for connections
        },
        echo=False                   # Set to True for SQL debugging
    )
except Exception as e:
    logger.critical(f"✗ Failed to configure database engine: {e}")
    raise

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Yields a scoped SQLAlchemy database session for use as a FastAPI dependency.

    Yields:
        Session: SQLAlchemy database session

    Raises:
        Exception: Propagates any exception raised by the route handler after
                   rolling back the session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
