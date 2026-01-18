"""
Database connection and session management
OPTIMIZED FOR PERFORMANCE: Added connection pooling configuration
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Only enable SQL query logging if explicitly enabled via environment variable
# This reduces console clutter and improves performance
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# Create database engine with optimized connection pool settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,          # Number of connections to keep in pool (default: 5)
    max_overflow=20,       # Max connections beyond pool_size (default: 10)
    pool_recycle=3600,     # Recycle connections after 1 hour to prevent stale connections
    echo=SQL_ECHO  # Disabled by default - set SQL_ECHO=true in .env to enable
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
