"""
Railway Database Configuration

This module handles Railway-specific database connections.
Railway provides DATABASE_URL with internal connection automatically.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


def get_railway_database_url() -> str:
    """
    Get database URL for Railway using internal networking only.
    Includes defensive cleaning for copy-paste typos.
    """
    url = None

    # 1. Try explicit private URL first
    private_url = os.getenv("DATABASE_PRIVATE_URL")
    if private_url:
        url = private_url
    # 2. Try the default DATABASE_URL
    elif settings.DATABASE_URL:
        url = settings.DATABASE_URL
    else:
        url = os.getenv("DATABASE_URL")

    if url:
        # DEFENSIVE: Remove accidental whitespace/quotes from copy-pasting
        url = url.strip().strip("'").strip('"')
        
        # SQLALCHEMY COMPATIBILITY: Fix 'postgres://' to 'postgresql://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        return url

    # Final fallback for local development
    return "postgresql://postgres:postgres@localhost:5432/ee_invoicing"


# Create engine with Railway-optimized settings
def create_railway_engine():
    """
    Create SQLAlchemy engine optimized for Railway.

    - Uses internal connection (provided by Railway)
    - Connection pooling for performance
    - Health checking
    - No SQL logging (security + performance)
    """
    db_url = get_railway_database_url()
    
    # Log connection attempt (sanitized)
    host = "unknown"
    if "@" in db_url:
        host = db_url.split("@")[1].split(":")[0]
    print(f"DEBUG: Attempting database connection to host: {host}")

    engine = create_engine(
        db_url,
        pool_pre_ping=True,           # Check connection health before using
        pool_recycle=3600,            # Recycle connections every hour
        pool_size=10,                  # Connection pool size
        max_overflow=20,                # Allow extra connections when needed
        echo=False,                     # Don't log SQL queries (security)
        connect_args={
            "connect_timeout": 10,      # Connection timeout
            "options": "-c statement_timeout=5000"  # Query timeout
        }
    )

    return engine


# Singleton engine instance
_engine = None


def get_engine():
    """
    Get database engine singleton.

    Returns:
        SQLAlchemy engine
    """
    global _engine
    if _engine is None:
        _engine = create_railway_engine()
    return _engine


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_engine()
)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> bool:
    """
    Check if database connection is healthy.

    This uses internal connection on Railway.

    Returns:
        True if database is connected, False otherwise
    """
    try:
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            # Simple query to test connection (text() wrapper required for SQLAlchemy 2.0+)
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        # Log error (don't expose connection details)
        print(f"Database health check failed: {type(e).__name__}")
        return False


def get_connection_info() -> dict:
    """
    Get database connection information (sanitized).

    Returns:
        Dictionary with connection info (URL not exposed)
    """
    engine = get_engine()

    # Parse connection URL (without exposing credentials)
    db_url = str(engine.url)
    is_railway = "railway.internal" in db_url or "railway.app" in db_url
    is_internal = "railway.internal" in db_url

    return {
        "is_railway": is_railway,
        "uses_internal_connection": is_internal,
        "database_name": engine.url.database,
        "host": engine.url.host if not is_internal else "railway.internal",
        "port": engine.url.port,
    }
