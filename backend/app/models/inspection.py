# app/models/inspection.py
#
# SQLAlchemy ORM model for the `inspection_records` table.
#
# One row = one quality inspection event for a lot.
# A lot may be inspected multiple times (re-inspection after a conditional pass).
# The `issue_flag` column is the primary signal used by AC5 and AC6:
#   • AC5: count issue_flag = True by production line to identify problem lines
#   • AC6: join flagged lots to shipping to check if they were shipped

from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class InspectionRecord(Base):
    """
    ORM model for the `inspection_records` table.

    Columns:
        inspection_id   : Surrogate PK.
        lot_id          : FK → lots.lot_id.
        inspection_date : Date the inspection was performed.
        inspection_result: 'Pass', 'Fail', or 'Conditional Pass'.
        issue_flag      : True when the inspection found a defect or concern.
                          This is the canonical "problem" indicator (AC5, AC6).
        inspector_notes : Free-text observations from the inspector.
        created_at/updated_at: Audit timestamps.
    """

    __tablename__ = "inspection_records"

    inspection_id     = Column(Integer, primary_key=True, index=True)
    lot_id            = Column(Integer, ForeignKey("lots.lot_id"), nullable=False, index=True)
    inspection_date   = Column(Date, nullable=False)
    inspection_result = Column(String(30), nullable=False)   # 'Pass' | 'Fail' | 'Conditional Pass'
    issue_flag        = Column(Boolean, nullable=False, default=False)
    inspector_notes   = Column(Text, nullable=True)

    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lot = relationship("Lot", back_populates="inspection_records")

    def __repr__(self) -> str:
        return (
            f"<InspectionRecord id={self.inspection_id} "
            f"lot={self.lot_id} result={self.inspection_result!r} flag={self.issue_flag}>"
        )
