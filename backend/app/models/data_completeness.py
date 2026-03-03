# app/models/data_completeness.py
#
# SQLAlchemy ORM model for the `data_completeness` table.
#
# In the PostgreSQL production database, this table is automatically maintained
# by three triggers (one per child table).  Whenever a production, inspection,
# or shipping record is inserted / updated / deleted, the trigger recalculates
# the completeness score for that lot and upserts a row here.
#
# In the test environment (SQLite), triggers don't fire, so the repository
# provides a Python function `refresh_data_completeness` (see repositories/)
# that performs the same calculation manually.  This keeps the business logic
# in one place and verifiable through unit tests.
#
# overall_completeness calculation:
#   score = ROUND((has_prod + has_insp + has_ship) / 3.0 * 100)
#   Possible values: 0, 33, 67, 100
#   Using ROUND (not truncation) so 2/3 → 67, not 66.

from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, SmallInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class DataCompleteness(Base):
    """
    ORM model for the `data_completeness` table.

    One row per lot — a derived summary of how complete that lot's data is
    across all three operational functions.  Supports AC4, AC8, AC9, AC10.

    Columns:
        lot_id               : PK and FK → lots.lot_id (one-to-one).
        has_production_data  : True if ≥1 production record exists for this lot.
        has_inspection_data  : True if ≥1 inspection record exists.
        has_shipping_data    : True if ≥1 shipping record exists.
        overall_completeness : Integer %; 0, 33, 67, or 100.
        last_evaluated_at    : When the row was last computed (business-visible
                               — analysts can see how fresh the score is).
    """

    __tablename__ = "data_completeness"

    lot_id                = Column(Integer, ForeignKey("lots.lot_id"), primary_key=True)

    has_production_data   = Column(Boolean, nullable=False, default=False)
    has_inspection_data   = Column(Boolean, nullable=False, default=False)
    has_shipping_data     = Column(Boolean, nullable=False, default=False)

    # SmallInteger (2 bytes) is sufficient for 0–100
    overall_completeness  = Column(SmallInteger, nullable=False, default=0)

    # Auto-set on insert; updated by triggers (or by refresh_data_completeness)
    last_evaluated_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Back-reference to the parent lot (one-to-one)
    lot = relationship("Lot", back_populates="data_completeness")

    def __repr__(self) -> str:
        return (
            f"<DataCompleteness lot={self.lot_id} "
            f"score={self.overall_completeness}% "
            f"P={self.has_production_data} I={self.has_inspection_data} S={self.has_shipping_data}>"
        )
