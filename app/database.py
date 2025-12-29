"""
Database connection module with resilient Railway support.
"""

from app.railway_db import (
    get_engine, 
    get_db as get_railway_db, 
    check_database_health, 
    get_connection_info, 
    Base, 
    SessionLocal,
    connect_with_retry
)

# Shared engine and session
engine = get_engine()

# Re-export for backward compatibility
def get_db():
    return get_railway_db()

__all__ = [
    'engine', 
    'SessionLocal', 
    'Base', 
    'get_db', 
    'check_database_health', 
    'get_connection_info',
    'connect_with_retry'
]
