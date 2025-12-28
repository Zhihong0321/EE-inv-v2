"""
Database connection module with Railway support.

This module uses Railway's internal database connection automatically.
On Railway, DATABASE_URL environment variable is provided with
private railway.internal connection for better security and performance.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import os

# Import Railway-specific database configuration
from app.railway_db import get_engine, get_db as get_railway_db, check_database_health, get_connection_info

# Create engine (using Railway configuration)
engine = get_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Re-export for backward compatibility
def get_db():
    """
    Dependency to get database session.

    This uses Railway's internal connection on Railway.

    Yields:
        Database session
    """
    return get_railway_db()


# Expose functions
__all__ = ['engine', 'SessionLocal', 'Base', 'get_db', 'check_database_health', 'get_connection_info']
