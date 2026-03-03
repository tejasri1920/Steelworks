# app/schemas/reports.py
#
# Pydantic schemas for the four report endpoints.
# Each schema mirrors one of the PostgreSQL views defined in schema.sql,
# but is computed by the Python repository layer so tests can run without
# PostgreSQL.
#
# Report ↔ AC mapping:
#   LotSummaryRow            → AC1, AC2, AC3, AC7, AC8
#   InspectionIssueRow       → AC5, AC6
#   IncompleteLotRow         → AC4, AC10
#   LineIssueRow             → AC5

from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime


class LotSummaryRow(BaseModel):
    """
    One row in the meeting-ready lot summary report (AC1, AC2, AC7, AC8).

    Aggregates all three functions into a single row per lot so that an
    analyst can get a full operational picture in one glance without
    opening multiple spreadsheets.

    Null fields indicate that function has no data for this lot (AC4).
    `overall_completeness` is the quick-glance data quality indicator (AC10).
    """

    # Lot identity
    lot_id:                  int
    lot_code:                str
    start_date:              date
    end_date:                Optional[date]    # NULL = lot still open

    # Production summary (NULL when has_production_data = False)
    has_production_data:     bool
    production_run_count:    int               # How many production runs
    total_units_produced:    Optional[int]     # Sum of quantity_produced; NULL if no runs
    total_units_planned:     Optional[int]
    attainment_pct:          Optional[float]   # (produced / planned) * 100; NULL if no runs
    total_downtime_min:      Optional[int]
    any_line_issue:          bool              # True if any run had an issue
    production_issue_count:  int               # Count of runs with line_issue = True

    # Inspection summary (NULL when has_inspection_data = False)
    has_inspection_data:     bool
    inspection_count:        int
    any_inspection_issue:    bool
    inspection_issue_count:  int

    # Shipping summary (NULL when has_shipping_data = False)
    has_shipping_data:       bool
    shipment_count:          int
    total_qty_shipped:       Optional[int]
    shipment_statuses:       List[str]         # Distinct statuses (e.g., ['Shipped', 'Partial'])
    any_shipment_blocked:    bool              # True if any shipment is On Hold or Backordered

    # Data completeness (AC4, AC10)
    overall_completeness:    int               # 0, 33, 67, or 100
    completeness_last_updated: Optional[datetime]


class InspectionIssueRow(BaseModel):
    """
    One row in the inspection-issues-with-shipping-status report (AC5, AC6).

    Shows every lot that had at least one flagged inspection, alongside its
    shipping status.  Answers: "Have lots with quality issues already shipped?"

    `ship_date` and `shipment_status` are NULL when the lot has no shipping
    record yet — the analyst can immediately see these lots have not been
    dispatched (AC4, AC6).
    """

    lot_id:             int
    lot_code:           str
    start_date:         date
    inspection_date:    date
    inspection_result:  str              # 'Fail' | 'Conditional Pass' (flagged)
    inspector_notes:    Optional[str]

    # Shipping info — NULL if the lot hasn't been shipped yet (AC6)
    ship_date:          Optional[date]
    shipment_status:    Optional[str]
    hold_reason:        Optional[str]
    customer:           Optional[str]
    destination:        Optional[str]

    overall_completeness: int


class IncompleteLotRow(BaseModel):
    """
    One row in the incomplete-lots report (AC4, AC10).

    Lists every lot that is missing data from at least one function, with a
    plain-English `completeness_note` explaining exactly what is absent.
    This is the "data quality" view the analyst checks before a meeting.
    """

    lot_id:               int
    lot_code:             str
    start_date:           date
    end_date:             Optional[date]
    has_production_data:  bool
    has_inspection_data:  bool
    has_shipping_data:    bool
    overall_completeness: int
    last_evaluated_at:    datetime
    completeness_note:    str    # e.g., "Missing inspection data"


class LineIssueRow(BaseModel):
    """
    One row in the issues-by-production-line report (AC5).

    Shows the total runs, flagged runs, issue rate, and breakdown by issue
    type for each production line.  Answers: "Which line had the most problems
    and what kind?"
    """

    production_line:          str    # 'Line 1' | 'Line 2' | 'Line 3' | 'Line 4'
    total_runs:               int    # All production runs on this line
    issue_runs:               int    # Runs where line_issue = True
    issue_rate_pct:           float  # issue_runs / total_runs * 100

    # Breakdown by root cause (counts per issue type)
    tool_wear_count:          int
    sensor_fault_count:       int
    material_shortage_count:  int
    changeover_delay_count:   int
    quality_hold_count:       int
    operator_training_count:  int
