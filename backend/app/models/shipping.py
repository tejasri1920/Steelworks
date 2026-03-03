# app/models/shipping.py
#
# SQLAlchemy ORM model for the `shipping_records` table.
#
# One row = one shipment dispatch event.
# A lot may have MULTIPLE shipping records (split shipments — e.g., partial
# delivery to meet a deadline while the rest ships later).
#
# Key for AC6: `shipment_status` tells us whether a lot with inspection
# issues has already left the building ('Shipped'), is partially out
# ('Partial'), is blocked ('On Hold'), or is waiting ('Backordered').
# `hold_reason` is required whenever shipment_status = 'On Hold'.

from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ShippingRecord(Base):
    """
    ORM model for the `shipping_records` table.

    Columns:
        shipping_id     : Surrogate PK.
        lot_id          : FK → lots.lot_id.
        ship_date       : Scheduled or actual dispatch date.
        shipment_status : 'Shipped' | 'Partial' | 'On Hold' | 'Backordered'.
        destination     : US state abbreviation (e.g., 'IA', 'OH').
        customer        : Who the shipment is going to.
        sales_order     : Sales order number (nullable — some rows had none).
        carrier         : Carrier name; NULL for customer pickup.
        bol_number      : Bill of Lading number; UNIQUE, nullable.
        tracking_pro    : Carrier tracking number.
        qty_shipped     : Quantity dispatched in this shipment (default 0).
        hold_reason     : Required when status = 'On Hold' (AC6 visibility).
        shipping_notes  : Free-text from the shipping team.
        created_at/updated_at: Audit timestamps.
    """

    __tablename__ = "shipping_records"

    shipping_id     = Column(Integer, primary_key=True, index=True)
    lot_id          = Column(Integer, ForeignKey("lots.lot_id"), nullable=False, index=True)
    ship_date       = Column(Date, nullable=False)
    shipment_status = Column(String(20), nullable=False)
    destination     = Column(String(5), nullable=False)     # State abbreviation
    customer        = Column(String(50), nullable=False)
    sales_order     = Column(String(20), nullable=True)
    carrier         = Column(String(50), nullable=True)     # NULL = customer pickup
    bol_number      = Column(String(20), nullable=True, unique=True)
    tracking_pro    = Column(String(50), nullable=True)
    qty_shipped     = Column(Integer, nullable=False, default=0)
    hold_reason     = Column(String(100), nullable=True)    # Must be set when On Hold
    shipping_notes  = Column(Text, nullable=True)

    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lot = relationship("Lot", back_populates="shipping_records")

    def __repr__(self) -> str:
        return (
            f"<ShippingRecord id={self.shipping_id} "
            f"lot={self.lot_id} status={self.shipment_status!r} date={self.ship_date}>"
        )
