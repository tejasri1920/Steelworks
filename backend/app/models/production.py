# app/models/production.py
#
# SQLAlchemy ORM model for the `production_records` table.
#
# One row represents a single production run: a specific lot being
# manufactured on a specific line during a specific shift on a given date.
# The combination (lot_id, production_date, shift, production_line) is unique
# — you can't have two runs for the same lot in the same slot.

from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DateTime, SmallInteger, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ProductionRecord(Base):
    """
    ORM model for the `production_records` table.

    Columns:
        production_id   : Surrogate PK, auto-incremented.
        lot_id          : FK → lots.lot_id.
        production_date : Date the run occurred.
        production_line : Which line ('Line 1'–'Line 4').
        part_number     : Part manufactured (e.g., 'SW-8091-A').
        units_planned   : Target output for this run.
        quantity_produced: Actual output; may be less than planned.
        downtime_min    : Minutes of unplanned downtime (default 0).
        shift           : 'Day', 'Swing', or 'Night'.
        line_issue      : True when a line problem was flagged.
        primary_issue   : Category of problem (only set when line_issue=True).
        supervisor_notes: Free-text from the shift supervisor.
        created_at/updated_at: Audit timestamps.
    """

    __tablename__ = "production_records"

    production_id     = Column(Integer, primary_key=True, index=True)

    # FK → lots.lot_id — NOT NULL because every production run belongs to a lot
    lot_id            = Column(Integer, ForeignKey("lots.lot_id"), nullable=False, index=True)

    production_date   = Column(Date, nullable=False)
    production_line   = Column(String(50), nullable=False)
    part_number       = Column(String(20), nullable=False)
    units_planned     = Column(Integer, nullable=False)
    quantity_produced = Column(Integer, nullable=False)

    # SmallInteger saves 2 bytes vs Integer; downtime rarely exceeds 32767 min
    downtime_min      = Column(SmallInteger, nullable=False, default=0)

    shift             = Column(String(20), nullable=False)

    # Boolean: True/False flag
    # Note: SQLite stores booleans as 0/1 integers; SQLAlchemy handles the
    # conversion transparently so Python code always sees True/False.
    line_issue        = Column(Boolean, nullable=False, default=False)

    # NULL when no issue was flagged (line_issue = False)
    primary_issue     = Column(String(50), nullable=True)
    supervisor_notes  = Column(Text, nullable=True)

    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to the parent Lot — lets you do `record.lot.lot_code`
    lot = relationship("Lot", back_populates="production_records")

    def __repr__(self) -> str:
        return (
            f"<ProductionRecord id={self.production_id} "
            f"lot={self.lot_id} date={self.production_date} line={self.production_line!r}>"
        )
