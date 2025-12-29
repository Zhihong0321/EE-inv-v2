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

# Deep Root Cause Fix: Wrap engine in a lazy proxy to prevent top-level import crashes
class LazyEngine:
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    def __repr__(self):
        return repr(get_engine())
    def __str__(self):
        return str(get_engine())

engine = LazyEngine()

# Re-export for backward compatibility
get_db = get_railway_db

__all__ = [
    'engine', 
    'SessionLocal', 
    'Base', 
    'get_db', 
    'check_database_health', 
    'get_connection_info',
    'connect_with_retry'
]
