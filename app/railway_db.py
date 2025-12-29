import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_railway_database_url() -> str:
    """
    Get database URL for Railway using internal networking only.
    Strict enforcement: No scammy localhost fallbacks in production.
    """
    # 1. Try OS Environment variables first
    url = os.environ.get("DATABASE_PRIVATE_URL") or os.environ.get("DATABASE_URL")
    
    # 2. Try Pydantic settings
    if not url:
        url = settings.DATABASE_PRIVATE_URL or settings.DATABASE_URL

    if not url:
        # If we are on Railway (RAILWAY_ENVIRONMENT set), fail loudly
        if os.environ.get("RAILWAY_ENVIRONMENT"):
            logger.critical("CRITICAL: DATABASE_URL is missing in Railway environment!")
            raise RuntimeError("Database configuration missing. Deployment will fail.")
        
        # Local development fallback
        return "postgresql://postgres:postgres@localhost:5432/ee_invoicing"

    # DEFENSIVE: Remove accidental whitespace/quotes
    url = url.strip().strip("'").strip('"')
    
    # SQLALCHEMY COMPATIBILITY: Fix 'postgres://' to 'postgresql://'
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    return url

def create_railway_engine():
    """Create SQLAlchemy engine with robust connection pooling."""
    db_url = get_railway_database_url()
    
    # Sanitized host logging
    host = db_url.split("@")[1].split(":")[0] if "@" in db_url else "unknown"
    logger.info(f"Configuring database engine for host: {host}")

    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000"
        }
    )

# Singleton instances
_engine = None
_SessionLocal = None

def get_engine():
    """Lazy engine initialization to prevent import-time crashes."""
    global _engine
    if _engine is None:
        _engine = create_railway_engine()
    return _engine

def get_session_local():
    """Lazy session initialization."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def SessionLocal(*args, **kwargs):
    """Backward compatible wrapper for lazy SessionLocal."""
    return get_session_local()(*args, **kwargs)

def connect_with_retry(max_retries=5, delay=3):
    """Exponential backoff for internal DNS/Network lag."""
    last_error = None
    for attempt in range(max_retries):
        try:
            # We wrap get_engine in try/except here to prevent boot crash
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully.")
                return True
        except Exception as e:
            last_error = e
            wait = delay * (attempt + 1)
            logger.warning(f"DB Connection attempt {attempt + 1} failed. Retrying in {wait}s...")
            time.sleep(wait)
    logger.error(f"Failed to connect: {last_error}")
    return False

# Base class for models
Base = declarative_base()

def get_db():
    Session = get_session_local()
    db = Session()
    try:
        yield db
    finally:
        db.close()

def check_database_health() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except:
        return False

def get_connection_info() -> dict:
    engine = get_engine()
    db_url = str(engine.url)
    is_internal = "railway.internal" in db_url
    return {
        "is_railway": "railway" in db_url,
        "uses_internal_connection": is_internal,
        "database_name": engine.url.database,
        "host": engine.url.host if not is_internal else "railway.internal",
        "port": engine.url.port,
    }
