import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Fix legacy postgres:// URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine with connection pooling for Render PostgreSQL
# This prevents "SSL connection has been closed unexpectedly" errors
connect_args = {}
if DATABASE_URL.startswith("postgresql://"):
    # Render PostgreSQL requires SSL, but DATABASE_URL usually includes SSL params
    # Add explicit SSL mode if not already in URL
    if "sslmode=" not in DATABASE_URL:
        connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Maximum number of connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using them (prevents stale connections)
    pool_recycle=300,  # Recycle connections after 5 minutes (prevents timeout issues)
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
