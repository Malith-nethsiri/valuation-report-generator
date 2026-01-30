from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

# Load environment files: .env first, then .env.local overrides
env_path = Path(__file__).parent.parent
load_dotenv(env_path / '.env')
load_dotenv(env_path / '.env.local', override=True)  # .env.local takes priority

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Validate DATABASE_URL exists
if not DATABASE_URL:
    logger.critical("DATABASE_URL environment variable is not set")
    raise RuntimeError("DATABASE_URL environment variable is required")

# Create SQLAlchemy engine with enhanced connection pooling and error handling
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

    # Test connection on startup
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("✓ Database connection established successfully")

except OperationalError as e:
    logger.critical(f"✗ Database connection failed: {e}")
    raise RuntimeError(f"Cannot connect to database. Please check DATABASE_URL configuration: {e}")
except Exception as e:
    logger.critical(f"✗ Unexpected database error: {e}")
    raise

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session with retry logic
def get_db():
    """
    Get database session with automatic retry on disconnection.

    Yields:
        Session: SQLAlchemy database session

    Raises:
        Exception: If database operations fail after retry
    """
    db = SessionLocal()
    try:
        yield db
    except DisconnectionError as e:
        logger.error(f"Database disconnection detected: {e}. Attempting reconnection...")
        db.rollback()
        db.close()
        # Create new session and retry
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
