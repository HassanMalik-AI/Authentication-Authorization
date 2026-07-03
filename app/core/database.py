from sqlalchemy import create_engine, event, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
import logging
from typing import Generator
from app.core.config import settings

logger = logging.getLogger(__name__)

# PostgreSQL Connection with SSL
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DB_ECHO,
    connect_args={
        "sslmode": settings.DB_SSL_MODE,
        "connect_timeout": 10,
        "application_name": settings.APP_NAME,
        "keepalives_idle": 5,
        "keepalives_interval": 2,
        "keepalives_count": 2
    }
)

# Enable Row Level Security (RLS)
@event.listens_for(engine, "connect")
def enable_rls(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET app.current_user_id = 0;")
    cursor.execute("SET app.current_user_role = 'guest';")
    cursor.execute("SET app.tenant_id = 1;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for database sessions with transaction handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Secure database functions
def enable_row_level_security():
    """Enable Row Level Security on all tables"""
    with get_db_context() as db:
        # Create RLS policy for users table
        db.execute("""
            ALTER TABLE users ENABLE ROW LEVEL SECURITY;
            CREATE POLICY user_access_policy ON users
                USING (tenant_id = current_setting('app.tenant_id')::int)
                WITH CHECK (tenant_id = current_setting('app.tenant_id')::int);
        """)
        db.commit()