# shared/database.py
"""
Shared database configuration for all services
Single database with schema-based separation
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import redis
from contextlib import contextmanager

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://eventix_user:eventix_password@localhost:5432/eventix"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# SQLAlchemy Engine with Connection Pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("ENVIRONMENT") == "development"
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Models
Base = declarative_base()

# Redis Connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session management"""
    
    @staticmethod
    def get_db():
        """Get database session"""
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    @contextmanager
    def get_db_context():
        """Get database session with context manager"""
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def health_check():
        """Check database health"""
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

class CacheManager:
    """Redis cache management"""
    
    @staticmethod
    def get(key: str):
        """Get value from cache"""
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: str, expire: int = 3600):
        """Set value in cache"""
        try:
            redis_client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @staticmethod
    def delete(key: str):
        """Delete key from cache"""
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    @staticmethod
    def health_check():
        """Check cache health"""
        try:
            redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False

# Schema-based table naming
def get_table_name(schema: str, table: str) -> str:
    """Generate schema-aware table name"""
    return f"{schema}.{table}"

# Migration helper
def create_all_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

# Connection testing
def test_connections():
    """Test all connections"""
    db_status = DatabaseManager.health_check()
    cache_status = CacheManager.health_check()
    
    logger.info(f"Database: {'✓' if db_status else '✗'}")
    logger.info(f"Cache: {'✓' if cache_status else '✗'}")
    
    return db_status and cache_status

if __name__ == "__main__":
    test_connections()