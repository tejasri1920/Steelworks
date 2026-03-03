# app/models/lot.py
#
# SQLAlchemy ORM model for the `lots` table.
#
# The `lots` table is the central entity — every production run, inspection
# event, and shipment references a lot by `lot_id`.  Think of a lot as a
# production batch: a quantity of a specific part produced together.
#
# Relationships declared here use SQLAlchemy's lazy-loading by default.
# In the repositories we use `selectinload` (see repositories/lot_repo.py)
# to eagerly load related records in a single extra query per collection,
# avoiding the N+1 query problem.
#
# N+1 problem explained: if you load 100 lots then access .production_records
# for each, SQLAlchemy fires 100 separate SELECT queries (1 per lot).
# `selectinload` fires just ONE query: `SELECT * FROM production_records
# WHERE lot_id IN (1, 2, … 100)`.

from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class Lot(Base):
    """
    ORM model for the `lots` table.

    One row = one production lot (a batch of a specific part).
    Every child record (production, inspection, shipping) foreign-keys to this.

    Columns:
        lot_id    : Surrogate primary key, auto-incremented by the database.
        lot_code  : Business identifier (e.g., 'LOT-20260112-001').
                    UNIQUE — the code the operations team uses in documents.
        start_date: Date the lot was opened / first produced.
        end_date  : Date the lot was closed; NULL while still open.
        created_at: Timestamp of the INSERT; set by the database default.
        updated_at: Timestamp of the last UPDATE; maintained by a trigger.
    """

    __tablename__ = "lots"

    # Primary key — auto-incremented integer
    lot_id     = Column(Integer, primary_key=True, index=True)

    # Business identifier — UNIQUE ensures no two lots share the same code.
    # VARCHAR(50) matches the schema definition; indexed for O(log n) lookup.
    lot_code   = Column(String(50), nullable=False, unique=True, index=True)

    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=True)   # NULL while lot is still open

    # Audit timestamps — set automatically; useful for debugging data freshness
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # "back_populates" creates a bidirectional link so that from a
    # ProductionRecord you can navigate to its lot via `.lot`.
    # `cascade="all, delete-orphan"` means deleting a Lot automatically
    # deletes its child records — mirrors ON DELETE RESTRICT in the DDL
    # (but kept here for test convenience; production enforces at DB level).
    # ------------------------------------------------------------------
    production_records  = relationship(
        "ProductionRecord",
        back_populates="lot",
        lazy="select",              # Don't load automatically; use selectinload in queries
    )
    inspection_records  = relationship(
        "InspectionRecord",
        back_populates="lot",
        lazy="select",
    )
    shipping_records    = relationship(
        "ShippingRecord",
        back_populates="lot",
        lazy="select",
    )
    data_completeness   = relationship(
        "DataCompleteness",
        back_populates="lot",
        uselist=False,              # One-to-one: each lot has exactly one completeness row
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Lot id={self.lot_id} code={self.lot_code!r}>"
