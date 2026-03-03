# app/schemas/lot.py
#
# Pydantic schemas for the Lot entity and the "lot detail" response that
# bundles all three functions together.
#
# The `LotDetail` schema (AC1, AC2, AC8) is the most important: it returns
# a single lot with all its production, inspection, and shipping records in
# one response.  The analyst no longer needs to open three spreadsheets.

from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime


# ── Nested schemas (returned inside LotDetail) ────────────────────────────────

class ProductionRecordSchema(BaseModel):
    """Represents one production run nested inside a LotDetail response."""
    model_config = ConfigDict(from_attributes=True)   # Read from ORM attributes

    production_id:    int
    production_date:  date
    production_line:  str
    part_number:      str
    units_planned:    int
    quantity_produced: int
    downtime_min:     int
    shift:            str
    line_issue:       bool
    primary_issue:    Optional[str]   # NULL when no issue was flagged
    supervisor_notes: Optional[str]


class InspectionRecordSchema(BaseModel):
    """Represents one inspection event nested inside a LotDetail response."""
    model_config = ConfigDict(from_attributes=True)

    inspection_id:    int
    inspection_date:  date
    inspection_result: str            # 'Pass' | 'Fail' | 'Conditional Pass'
    issue_flag:       bool
    inspector_notes:  Optional[str]


class ShippingRecordSchema(BaseModel):
    """Represents one shipment event nested inside a LotDetail response."""
    model_config = ConfigDict(from_attributes=True)

    shipping_id:      int
    ship_date:        date
    shipment_status:  str             # 'Shipped' | 'Partial' | 'On Hold' | 'Backordered'
    destination:      str
    customer:         str
    sales_order:      Optional[str]
    carrier:          Optional[str]   # NULL = customer pickup
    bol_number:       Optional[str]
    tracking_pro:     Optional[str]
    qty_shipped:      int
    hold_reason:      Optional[str]   # Non-null when On Hold (AC6)
    shipping_notes:   Optional[str]


class CompletenessSchema(BaseModel):
    """Data completeness summary for a lot (AC4, AC10)."""
    model_config = ConfigDict(from_attributes=True)

    has_production_data:  bool
    has_inspection_data:  bool
    has_shipping_data:    bool
    overall_completeness: int         # 0, 33, 67, or 100
    last_evaluated_at:    datetime


# ── Primary schemas ────────────────────────────────────────────────────────────

class LotSummary(BaseModel):
    """
    Lightweight lot listing item — used for the lot list endpoint.
    Does not include child records (use LotDetail for those).
    """
    model_config = ConfigDict(from_attributes=True)

    lot_id:     int
    lot_code:   str
    start_date: date
    end_date:   Optional[date]        # NULL while lot is open


class LotDetail(BaseModel):
    """
    Full lot view with all three functions' records (AC1, AC2, AC8).

    This is the "meeting-ready" single-lot view: one API call returns
    everything an analyst needs for a specific lot without opening
    any spreadsheets.

    Fields:
        lot_id, lot_code, start_date, end_date:  identity columns.
        production_records:  all production runs for this lot.
        inspection_records:  all inspection events for this lot.
        shipping_records:    all shipment events for this lot.
        completeness:        data coverage summary (AC4, AC10).
    """
    model_config = ConfigDict(from_attributes=True)

    lot_id:              int
    lot_code:            str
    start_date:          date
    end_date:            Optional[date]

    # LEFT JOINs: these lists may be empty if a function has no records yet.
    # AC4: empty lists + completeness.has_*_data = False signals missing data.
    production_records:  List[ProductionRecordSchema] = []
    inspection_records:  List[InspectionRecordSchema] = []
    shipping_records:    List[ShippingRecordSchema]   = []

    # May be None if this lot has no data_completeness row yet
    completeness:        Optional[CompletenessSchema]
