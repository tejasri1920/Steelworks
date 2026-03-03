# app/database.py
#
# SQLAlchemy database setup: engine, session factory, and the ORM Base class.
#
# Key concepts for juniors:
#   - Engine: the low-level connection pool to the database.
#   - Session: a unit-of-work object. One session per HTTP request.
#     It tracks all ORM objects, buffers writes, and commits or rolls back
#     as a transaction. Sessions are NOT thread-safe, so each request gets
#     its own (via FastAPI's dependency injection).
#   - Base: the declarative base class from which all ORM models inherit.
#     SQLAlchemy uses it to discover table definitions and build the schema.
#
# The `get_db` generator is a FastAPI dependency that:
#   1. Opens a new session at the start of every request
#   2. Yields it to the route handler
#   3. Closes (and thereby releases the connection back to the pool)
#      in the `finally` block — so resources are freed even on errors.

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# ---------------------------------------------------------------------------
# SQLite compatibility shim
# ---------------------------------------------------------------------------
# When TESTING=true, the test suite uses SQLite instead of PostgreSQL so tests
# run without a running database container.
#
# SQLite requires `check_same_thread=False` because SQLAlchemy uses a
# connection pool and may hand a connection to a different thread than the one
# that created it.  This is safe because we use sessions correctly.
#
# For PostgreSQL we pass `options=-c search_path=ops` so that unqualified
# table names (e.g., `lots`) resolve to the `ops` schema automatically.
# ---------------------------------------------------------------------------

def _build_engine():
    """
    Factory function that creates the SQLAlchemy Engine appropriate for the
    current environment (PostgreSQL in production, SQLite in tests).

    Returns:
        Engine: a configured SQLAlchemy Engine instance.

    Time complexity: O(1) — just constructs the engine object; no queries run.
    """
    if settings.is_testing:
        # SQLite in-memory database for tests.
        # The database is destroyed when the engine is garbage-collected,
        # so each test module gets a clean slate.
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            # echo=True prints every SQL statement — helpful for debugging tests
        )

        # SQLite does not enforce foreign keys by default.
        # This listener enables FK enforcement on each new connection so that
        # test failures surface constraint violations the same way PostgreSQL would.
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
    else:
        # PostgreSQL for production / staging.
        # `options=-c search_path=ops` makes every connection's default schema
        # point to the `ops` namespace, so all ORM models work without
        # explicit schema prefixes in their table definitions.
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"options": "-c search_path=ops"},
            # Connection pool settings:
            pool_pre_ping=True,   # Send a lightweight "is connection alive?" check before use
            pool_size=5,          # Keep 5 idle connections ready (reduces connection overhead)
            max_overflow=10,      # Allow up to 10 additional connections under high load
        )
        return engine


# Module-level engine — shared across all requests
engine = _build_engine()

# Session factory — call SessionLocal() to get a new session
# autocommit=False: changes must be explicitly committed (safer default)
# autoflush=False:  don't auto-flush before queries (we control when that happens)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All model classes inherit from this so SQLAlchemy can discover table
    definitions via `Base.metadata.create_all(engine)`.

    Example:
        class Lot(Base):
            __tablename__ = "lots"
            lot_id = Column(Integer, primary_key=True)
    """
    pass


def get_db():
    """
    FastAPI dependency that provides a database session per HTTP request.

    Usage in a router:
        @router.get("/lots")
        def list_lots(db: Session = Depends(get_db)):
            ...

    The `yield` makes this a generator dependency.  FastAPI runs everything
    before the yield at request start, and everything after yield (the
    `finally` block) at request end — even if an exception was raised.
    This guarantees the session is always closed, preventing connection leaks.

    Yields:
        Session: an active SQLAlchemy session bound to the current request.
    """
    db = SessionLocal()
    try:
        yield db          # Control returns here for the duration of the request
    finally:
        db.close()        # ← Connection released back to pool here; prevents leaks
