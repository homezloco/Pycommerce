"""
Database configuration for PyCommerce.

This module configures the SQLAlchemy engine and session for the application.
"""

import os
import time
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)

# Create a base class for declarative models
convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s'
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pycommerce")

# Initialize SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create thread-local session
db_session = scoped_session(SessionLocal)


def get_db() -> scoped_session:
    """Get a database session."""
    return db_session


def init_db():
    """Initialize the database connection with retry logic."""
    global engine, Session

    # Get database URL from environment variable or use SQLite as fallback
    database_url = os.environ.get("DATABASE_URL")
    if database_url is None:
        logger.warning("DATABASE_URL not set, using SQLite by default")
        database_url = "sqlite:///pycommerce.db"

    # Maximum number of retry attempts
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            if engine is None:
                logger.info(f"Connecting to database (attempt {attempt+1}/{max_retries})...")

                # Create engine with connection pool settings
                engine = create_engine(
                    database_url,
                    pool_pre_ping=True,  # Test connections before use
                    pool_recycle=3600,   # Recycle connections every hour
                    connect_args={
                        "connect_timeout": 10,  # Timeout after 10 seconds
                    } if 'postgresql' in database_url else {}
                )

                # Create session factory
                Session = sessionmaker(bind=engine)

                # Create tables
                Base.metadata.create_all(bind=engine, checkfirst=True)

                logger.info(f"Connected to database: {database_url.split('@')[-1]}")
                return True
            return True
        except Exception as e:
            logger.error(f"Error initializing database (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Maximum retry attempts reached. Could not connect to database.")
                return False


def close_db() -> None:
    """Close the database session."""
    db_session.remove()


def get_session():
    """
    Get a session context manager.

    This function returns a context manager for database sessions,
    ensuring they are properly closed after use.

    Example:
        with get_session() as session:
            result = session.query(Model).all()
    """
    return DBSessionContext()


class DBSessionContext:
    """Context manager for database sessions."""

    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

def get_db():
    """Get a database session with error handling.

    Returns:
        SQLAlchemy Session: A new database session
    """
    if engine is None:
        if not init_db():
            raise Exception("Failed to initialize database connection")

    session = Session()
    try:
        # Test the connection
        session.execute("SELECT 1")
        return session
    except Exception as e:
        session.close()
        logger.error(f"Error getting database session: {str(e)}")

        # Try to reinitialize the connection
        if init_db():
            # Return a new session if reinitialization was successful
            return Session()
        else:
            raise Exception("Failed to reconnect to database")