# app/repositories/lot_repo.py
#
# Data-access functions for the `lots` table and its related child records.
#
# Pattern: each function accepts a SQLAlchemy Session (`db`) and query
# parameters.  It returns ORM model instances (or None/raises if not found).
# The router layer then converts ORM objects to Pydantic schemas for the
# HTTP response.
#
# Complexity notes use:
#   n = number of matching lots
#   p = production records per lot (average)
#   i = inspection records per lot (average)
#   s = shipping records per lot (average)

from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session, selectinload

from app.models.lot import Lot
from app.models.production import ProductionRecord
from app.models.inspection import InspectionRecord
from app.models.shipping import ShippingRecord
from app.models.data_completeness import DataCompleteness


def get_lots(
    db: Session,
    lot_code:  Optional[str]  = None,
    date_from: Optional[date] = None,
    date_to:   Optional[date] = None,
    skip:      int            = 0,
    limit:     int            = 100,
) -> List[Lot]:
    """
    Return a paginated list of lots matching the given filters.

    Each Lot is returned WITHOUT eagerly loading child records (faster for
    list views — the detail endpoint loads children separately).

    Args:
        db:        Active SQLAlchemy session (injected by FastAPI's Depends).
        lot_code:  Exact lot code match (case-sensitive).  Supports AC2.
        date_from: Only include lots whose start_date ≥ this date.  AC3.
        date_to:   Only include lots whose start_date ≤ this date.  AC3.
        skip:      Offset for pagination (skip first N records).
        limit:     Maximum records to return (page size).

    Returns:
        List of Lot ORM objects; empty list if no match.

    Time complexity: O(log n) for indexed lot_code lookup; O(n) for date
        range scan (with the idx_lots_dates composite index, this is
        O(log n + k) where k = matching rows — efficient for large tables).
    Space complexity: O(k) where k = rows returned.
    """
    query = db.query(Lot)

    # Apply filters — each adds a WHERE clause; indexes make these O(log n)
    if lot_code:
        # Exact match on the UNIQUE lot_code index → O(log n) B-tree lookup
        query = query.filter(Lot.lot_code == lot_code)

    if date_from:
        # Uses idx_lots_dates composite index
        query = query.filter(Lot.start_date >= date_from)

    if date_to:
        query = query.filter(Lot.start_date <= date_to)

    # Deterministic ordering so the same query always returns the same sequence
    # (AC9 — consistent results).  lot_id is the natural sort key.
    return query.order_by(Lot.lot_id).offset(skip).limit(limit).all()


def get_lot_by_code(db: Session, lot_code: str) -> Optional[Lot]:
    """
    Return a single Lot with ALL related records eagerly loaded.

    Uses `selectinload` for each child relationship.  This fires one
    extra SELECT per relationship (total: 4 SELECTs for the 3 child tables
    + the lots table itself), which is much better than:
      - Lazy loading: N+1 queries (one per attribute access)
      - Joined loading: a massive Cartesian product (production × inspection
        × shipping rows → many duplicate lot columns returned from the DB)

    Query plan (4 total SELECTs):
      1. SELECT * FROM lots WHERE lot_code = ?         → O(log n) on UNIQUE index
      2. SELECT * FROM production_records WHERE lot_id IN (?)  → O(p)
      3. SELECT * FROM inspection_records  WHERE lot_id IN (?) → O(i)
      4. SELECT * FROM shipping_records    WHERE lot_id IN (?) → O(s)
      5. SELECT * FROM data_completeness   WHERE lot_id IN (?) → O(1) (one row per lot)

    Args:
        db:       Active SQLAlchemy session.
        lot_code: The business lot code (e.g., 'LOT-20260112-001').

    Returns:
        Lot ORM object with .production_records, .inspection_records,
        .shipping_records, .data_completeness populated.
        None if no lot with that code exists.

    Time complexity: O(log n + p + i + s) — dominated by indexed lookups.
    Space complexity: O(p + i + s) — holds all child records in memory.
    """
    return (
        db.query(Lot)
        .options(
            selectinload(Lot.production_records),    # Loads all production runs in 1 query
            selectinload(Lot.inspection_records),    # Loads all inspections in 1 query
            selectinload(Lot.shipping_records),      # Loads all shipments in 1 query
            selectinload(Lot.data_completeness),     # Loads completeness row in 1 query
        )
        .filter(Lot.lot_code == lot_code)
        .first()   # Returns None if not found — caller checks for 404
    )


def refresh_data_completeness(db: Session, lot_id: int) -> DataCompleteness:
    """
    Compute and upsert the data_completeness row for the given lot.

    In production (PostgreSQL), this is done automatically by database
    triggers after any INSERT/UPDATE/DELETE on the three child tables.
    In the test environment (SQLite), triggers don't exist, so tests
    call this function manually after inserting test data.

    Algorithm:
      1. Check existence in each child table with EXISTS (O(log n) per table).
      2. Compute integer score = ROUND((has_p + has_i + has_s) / 3 * 100).
         ROUND is used (not truncation) so 2/3 → 67, not 66.
      3. Upsert into data_completeness (insert or overwrite existing row).

    Args:
        db:     Active SQLAlchemy session.
        lot_id: The lot to compute completeness for.

    Returns:
        The upserted DataCompleteness ORM object.

    Time complexity: O(log n) per EXISTS check (3 checks) → O(log n) overall.
    Space complexity: O(1).
    """
    # Each EXISTS stops at the first matching row — no COUNT(*) scan needed
    has_prod = db.query(
        db.query(ProductionRecord)
        .filter(ProductionRecord.lot_id == lot_id)
        .exists()
    ).scalar()

    has_insp = db.query(
        db.query(InspectionRecord)
        .filter(InspectionRecord.lot_id == lot_id)
        .exists()
    ).scalar()

    has_ship = db.query(
        db.query(ShippingRecord)
        .filter(ShippingRecord.lot_id == lot_id)
        .exists()
    ).scalar()

    # Convert booleans to 0/1 for arithmetic.  ROUND ensures 2/3 → 67 not 66.
    score = round((int(has_prod) + int(has_insp) + int(has_ship)) / 3 * 100)

    # Look for an existing row (upsert pattern)
    existing = db.query(DataCompleteness).filter(DataCompleteness.lot_id == lot_id).first()

    if existing:
        # UPDATE the existing row in place
        existing.has_production_data  = has_prod
        existing.has_inspection_data  = has_insp
        existing.has_shipping_data    = has_ship
        existing.overall_completeness = score
    else:
        # INSERT a new row
        existing = DataCompleteness(
            lot_id=lot_id,
            has_production_data=has_prod,
            has_inspection_data=has_insp,
            has_shipping_data=has_ship,
            overall_completeness=score,
        )
        db.add(existing)

    db.flush()     # Write to DB within the current transaction but don't commit yet
    return existing
