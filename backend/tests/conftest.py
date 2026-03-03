# tests/conftest.py
#
# Pytest configuration file — fixtures defined here are available to ALL
# test files in the tests/ directory without explicit imports.
#
# Test database strategy:
#   We use SQLite in-memory (sqlite:///:memory:) so tests run without a live
#   PostgreSQL container.  SQLAlchemy abstracts the database differences, so
#   the same ORM models, repository functions, and routers work with both.
#
# Key fixtures:
#   engine        – creates all tables in SQLite at test-session start
#   db_session    – one transactional session per test (rolled back after each)
#   client        – FastAPI TestClient with the DB dependency overridden
#   seeded_db     – pre-populated session ready for report assertions
#
# AC coverage note:
#   The fixtures provide data patterns that cover ALL 10 ACs.  Specifically:
#     - LOT-A has all three functions → AC1, AC2, AC7, AC8, AC9
#     - LOT-B has only production and shipping (no inspection) → AC4, AC10
#     - LOT-C has a flagged inspection with an On Hold shipment → AC5, AC6
#     - LOT-D has no records at all (completeness = 0) → AC4, AC10
#     - Date range: LOT-A starts 2026-01-10, LOT-B on 2026-01-15 → AC3

import os
import pytest
from datetime import date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from fastapi.testclient import TestClient

# Set TESTING flag BEFORE importing app modules so config.is_testing = True
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"   # fallback; not used by engine fixture

from app.main import app
from app.database import Base, get_db
from app.models import *   # noqa: F403  — ensures all ORM models are registered with Base.metadata
from app.models.lot import Lot
from app.models.production import ProductionRecord
from app.models.inspection import InspectionRecord
from app.models.shipping import ShippingRecord
from app.models.data_completeness import DataCompleteness
from app.repositories.lot_repo import refresh_data_completeness


# ---------------------------------------------------------------------------
# Session-scoped engine
# ---------------------------------------------------------------------------
# "session" scope = created once per pytest run, shared across all test files.
# This avoids re-creating the schema for every test, keeping the suite fast.

@pytest.fixture(scope="session")
def engine():
    """
    Create a SQLite in-memory engine and build the schema.

    SQLite in-memory databases are destroyed when all connections are closed.
    Using `scope="session"` keeps the connection alive for the full test run.

    Yields:
        Engine — the SQLAlchemy engine bound to :memory:

    Cleanup:
        `Base.metadata.drop_all` removes all tables (mainly for documentation;
         the in-memory DB is already gone when the engine is GC'd).
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Enable foreign key enforcement in SQLite (off by default)
    @event.listens_for(test_engine, "connect")
    def _enable_fk(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables defined in ORM models
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Teardown: drop all tables at the end of the test session
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Function-scoped database session
# ---------------------------------------------------------------------------
# Each test gets a fresh transaction that is rolled back after the test.
# This isolates tests from each other — inserts in test_A don't affect test_B.

@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """
    Provide a transactional SQLAlchemy session that rolls back after each test.

    How it works:
      - Begin a connection-level transaction (SAVEPOINT).
      - Pass the session to the test.
      - After the test, ROLLBACK discards all changes.
      - The next test starts from a clean state.

    Yields:
        Session — an active, transactional SQLAlchemy session.
    """
    connection = engine.connect()
    transaction = connection.begin()   # Begin a transaction

    TestingSession = sessionmaker(bind=connection)
    session = TestingSession()

    yield session

    session.close()
    transaction.rollback()   # ← Undo all inserts/updates from this test
    connection.close()       # ← Return connection to pool; prevents leaks


# ---------------------------------------------------------------------------
# FastAPI TestClient with DB override
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(engine) -> TestClient:
    """
    Return a FastAPI TestClient that uses the SQLite test engine.

    FastAPI's dependency injection is overridden so that every route handler
    that calls `Depends(get_db)` gets a session from our test engine instead
    of the production PostgreSQL engine.

    Yields:
        TestClient — makes HTTP requests to the FastAPI app in-process.
    """
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        """Replacement dependency that yields a test DB session."""
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()   # ← Always close the session; prevents connection leaks

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()   # Restore original dependency after test


# ---------------------------------------------------------------------------
# Seeded database fixture
# ---------------------------------------------------------------------------
# Inserts a minimal but representative dataset that covers all 10 ACs.
# All insertions happen within a transaction that is rolled back after each
# test that uses this fixture (because db_session is function-scoped).

@pytest.fixture(scope="function")
def seeded_db(db_session: Session) -> Session:
    """
    Insert four lots with varied data coverage, then return the session.

    Data design:
      LOT-A: All three functions present; no issues.          → AC1, AC2, AC8, AC9
      LOT-B: Production + Shipping; inspection MISSING.       → AC4, AC10
      LOT-C: All three; inspection FLAGGED + shipping On Hold.→ AC5, AC6
      LOT-D: No records (brand-new lot; completeness = 0).    → AC4, AC10

      Date spread: LOT-A 2026-01-10, LOT-B 2026-01-15, LOT-C 2026-01-12
                   → AC3 (date range filtering)

    Returns:
        Session — the same session with all test data flushed (not committed).
    """
    db = db_session

    # ── 1. Lots ──────────────────────────────────────────────────────────────
    lot_a = Lot(lot_code="LOT-A", start_date=date(2026, 1, 10))
    lot_b = Lot(lot_code="LOT-B", start_date=date(2026, 1, 15))
    lot_c = Lot(lot_code="LOT-C", start_date=date(2026, 1, 12))
    lot_d = Lot(lot_code="LOT-D", start_date=date(2026, 1, 20))  # no child records
    db.add_all([lot_a, lot_b, lot_c, lot_d])
    db.flush()   # Assigns lot_id values without committing

    # ── 2. Production records ─────────────────────────────────────────────────
    # LOT-A: clean run on Line 1
    pr_a = ProductionRecord(
        lot_id=lot_a.lot_id, production_date=date(2026, 1, 10),
        production_line="Line 1", part_number="SW-001-A",
        units_planned=300, quantity_produced=290, downtime_min=5,
        shift="Day", line_issue=False,
    )
    # LOT-B: clean run on Line 2
    pr_b = ProductionRecord(
        lot_id=lot_b.lot_id, production_date=date(2026, 1, 15),
        production_line="Line 2", part_number="SW-002-B",
        units_planned=200, quantity_produced=195, downtime_min=0,
        shift="Night", line_issue=False,
    )
    # LOT-C: issue run on Line 1 (sensor fault) — feeds AC5 (Line 1 issues)
    pr_c = ProductionRecord(
        lot_id=lot_c.lot_id, production_date=date(2026, 1, 12),
        production_line="Line 1", part_number="SW-003-C",
        units_planned=400, quantity_produced=350, downtime_min=60,
        shift="Swing", line_issue=True, primary_issue="Sensor fault",
        supervisor_notes="Sensor replaced mid-shift",
    )
    db.add_all([pr_a, pr_b, pr_c])
    db.flush()

    # ── 3. Inspection records ─────────────────────────────────────────────────
    # LOT-A: clean inspection
    ir_a = InspectionRecord(
        lot_id=lot_a.lot_id, inspection_date=date(2026, 1, 11),
        inspection_result="Pass", issue_flag=False,
    )
    # LOT-C: flagged inspection (Fail) — LOT-C should appear in inspection-issues report
    ir_c = InspectionRecord(
        lot_id=lot_c.lot_id, inspection_date=date(2026, 1, 13),
        inspection_result="Fail", issue_flag=True,
        inspector_notes="Dimensional out-of-spec",
    )
    # LOT-B intentionally has NO inspection record → has_inspection_data = False
    db.add_all([ir_a, ir_c])
    db.flush()

    # ── 4. Shipping records ───────────────────────────────────────────────────
    # LOT-A: shipped cleanly
    sr_a = ShippingRecord(
        lot_id=lot_a.lot_id, ship_date=date(2026, 1, 14),
        shipment_status="Shipped", destination="OH",
        customer="Acme Rail", qty_shipped=290,
    )
    # LOT-B: shipped (no inspection data — partial coverage)
    sr_b = ShippingRecord(
        lot_id=lot_b.lot_id, ship_date=date(2026, 1, 18),
        shipment_status="Shipped", destination="IA",
        customer="Prairie Pumps", qty_shipped=195,
    )
    # LOT-C: On Hold (inspection flagged + not yet shipped — AC6 key scenario)
    sr_c = ShippingRecord(
        lot_id=lot_c.lot_id, ship_date=date(2026, 1, 20),
        shipment_status="On Hold", destination="IL",
        customer="NorthStar Ag", qty_shipped=0,
        hold_reason="Quality hold pending reinspection",  # hold_reason required when On Hold
    )
    # LOT-D has no shipping record → has_shipping_data = False
    db.add_all([sr_a, sr_b, sr_c])
    db.flush()

    # ── 5. Data completeness (manually since SQLite has no triggers) ──────────
    refresh_data_completeness(db, lot_a.lot_id)   # has P, I, S → 100%
    refresh_data_completeness(db, lot_b.lot_id)   # has P, S; no I → 67%
    refresh_data_completeness(db, lot_c.lot_id)   # has P, I, S → 100%
    refresh_data_completeness(db, lot_d.lot_id)   # no children → 0%
    db.flush()

    return db


@pytest.fixture(scope="function")
def seeded_client(engine, seeded_db) -> TestClient:
    """
    A FastAPI TestClient backed by the already-seeded test database.

    This fixture combines `seeded_db` (data inserted) with `client` (HTTP
    client).  Use it in tests that make HTTP requests and need pre-existing
    data in the database.
    """
    # We need to share the same connection/session that seeded_db used,
    # so we bind the override to the seeded_db's connection.
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        # Return the already-seeded session so HTTP tests see the data
        yield seeded_db   # same session = same transaction = sees seeded data

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
