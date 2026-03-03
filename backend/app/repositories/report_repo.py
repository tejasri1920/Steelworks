# app/repositories/report_repo.py
#
# Data-access functions that power the four report endpoints.
# These implement the same logic as the PostgreSQL views in schema.sql but
# using Python + SQLAlchemy so they are testable with SQLite.
#
# View ↔ Python function mapping:
#   v_lot_summary                 → get_lot_summary()
#   v_inspection_issue_shipping   → get_inspection_issue_shipping()
#   v_incomplete_lots             → get_incomplete_lots()
#   v_issues_by_production_line   → get_line_issues()
#
# Design choice — Python aggregation vs. raw SQL view:
#   The PostgreSQL views use ARRAY_AGG, BOOL_OR, and FILTER, which are
#   PostgreSQL-specific.  Rather than write database-specific SQL, this
#   module uses SQLAlchemy's cross-database aggregate functions and
#   Python-level grouping, making the code testable without PostgreSQL.

from datetime import date, datetime
from typing import Optional, List
from collections import defaultdict

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.models.lot import Lot
from app.models.production import ProductionRecord
from app.models.inspection import InspectionRecord
from app.models.shipping import ShippingRecord
from app.models.data_completeness import DataCompleteness
from app.schemas.reports import (
    LotSummaryRow,
    InspectionIssueRow,
    IncompleteLotRow,
    LineIssueRow,
)


def get_lot_summary(
    db:        Session,
    lot_code:  Optional[str]  = None,
    date_from: Optional[date] = None,
    date_to:   Optional[date] = None,
) -> List[LotSummaryRow]:
    """
    Return one LotSummaryRow per lot, aggregating all three functions.

    Implements the same logic as `ops.v_lot_summary` (schema.sql §10a).
    Each row is a meeting-ready snapshot: production totals, inspection
    flags, shipping status, and completeness score — with no spreadsheet
    cross-referencing needed (AC1, AC2, AC7, AC8).

    Strategy:
      1. Query lots with optional filters (O(log n) with index).
      2. Eagerly load all four relationships in 4 extra SELECTs (selectinload).
      3. Aggregate in Python — portable, readable, and testable.

    Args:
        db:        Active SQLAlchemy session.
        lot_code:  Filter to a single lot code (AC2).
        date_from: Include only lots with start_date ≥ this value (AC3).
        date_to:   Include only lots with start_date ≤ this value (AC3).

    Returns:
        List of LotSummaryRow, ordered by lot_id (deterministic — AC9).

    Time complexity: O(n · (p + i + s)) where n = matching lots,
        p/i/s = average child records per lot.
    Space complexity: O(n · (p + i + s)) — all rows held in memory.
        For millions of rows, add server-side pagination.
    """
    query = (
        db.query(Lot)
        .options(
            selectinload(Lot.production_records),
            selectinload(Lot.inspection_records),
            selectinload(Lot.shipping_records),
            selectinload(Lot.data_completeness),
        )
    )

    # Apply filters (same logic as get_lots in lot_repo.py, supporting AC3)
    if lot_code:
        query = query.filter(Lot.lot_code == lot_code)
    if date_from:
        query = query.filter(Lot.start_date >= date_from)
    if date_to:
        query = query.filter(Lot.start_date <= date_to)

    lots = query.order_by(Lot.lot_id).all()

    rows: List[LotSummaryRow] = []
    for lot in lots:
        pr_list = lot.production_records   # List[ProductionRecord]
        ir_list = lot.inspection_records   # List[InspectionRecord]
        sr_list = lot.shipping_records     # List[ShippingRecord]
        dc      = lot.data_completeness    # DataCompleteness | None

        # ── Production aggregates ─────────────────────────────────────────
        # O(p) per lot — iterates once through production records
        total_produced  = sum(r.quantity_produced for r in pr_list) if pr_list else None
        total_planned   = sum(r.units_planned     for r in pr_list) if pr_list else None
        total_downtime  = sum(r.downtime_min      for r in pr_list) if pr_list else None
        issue_runs      = [r for r in pr_list if r.line_issue]
        any_line_issue  = len(issue_runs) > 0

        # Attainment % = actual / planned × 100; NULLIF guard: skip if planned = 0
        attainment_pct: Optional[float] = None
        if total_planned and total_planned > 0 and total_produced is not None:
            attainment_pct = round(total_produced / total_planned * 100, 1)

        # ── Inspection aggregates ─────────────────────────────────────────
        # O(i) per lot
        flagged_insp         = [r for r in ir_list if r.issue_flag]
        any_inspection_issue = len(flagged_insp) > 0

        # ── Shipping aggregates ───────────────────────────────────────────
        # O(s) per lot
        total_qty_shipped   = sum(r.qty_shipped for r in sr_list) if sr_list else None
        # Unique statuses — equivalent to ARRAY_AGG(DISTINCT shipment_status)
        shipment_statuses   = list({r.shipment_status for r in sr_list})
        any_blocked         = any(
            r.shipment_status in ("On Hold", "Backordered") for r in sr_list
        )

        # ── Completeness ──────────────────────────────────────────────────
        has_prod = dc.has_production_data   if dc else bool(pr_list)
        has_insp = dc.has_inspection_data   if dc else bool(ir_list)
        has_ship = dc.has_shipping_data     if dc else bool(sr_list)
        overall  = dc.overall_completeness  if dc else round(
            (int(has_prod) + int(has_insp) + int(has_ship)) / 3 * 100
        )

        rows.append(LotSummaryRow(
            lot_id                = lot.lot_id,
            lot_code              = lot.lot_code,
            start_date            = lot.start_date,
            end_date              = lot.end_date,
            has_production_data   = has_prod,
            production_run_count  = len(pr_list),
            total_units_produced  = total_produced,
            total_units_planned   = total_planned,
            attainment_pct        = attainment_pct,
            total_downtime_min    = total_downtime,
            any_line_issue        = any_line_issue,
            production_issue_count= len(issue_runs),
            has_inspection_data   = has_insp,
            inspection_count      = len(ir_list),
            any_inspection_issue  = any_inspection_issue,
            inspection_issue_count= len(flagged_insp),
            has_shipping_data     = has_ship,
            shipment_count        = len(sr_list),
            total_qty_shipped     = total_qty_shipped,
            shipment_statuses     = shipment_statuses,
            any_shipment_blocked  = any_blocked,
            overall_completeness  = overall,
            completeness_last_updated = dc.last_evaluated_at if dc else None,
        ))

    return rows


def get_inspection_issue_shipping(
    db:        Session,
    lot_code:  Optional[str]  = None,
    date_from: Optional[date] = None,
    date_to:   Optional[date] = None,
) -> List[InspectionIssueRow]:
    """
    Return lots that have at least one flagged inspection, with their
    shipping records (AC5, AC6).

    Implements `ops.v_inspection_issue_shipping` (schema.sql §10b).

    Answers: "Have lots with quality problems already shipped?"
    - Rows with `ship_date = None` = lot not yet dispatched.
    - Rows with `shipment_status = 'On Hold'` = explicitly blocked.
    - Rows with `shipment_status = 'Shipped'` = already gone (AC6 concern).

    A lot may appear MULTIPLE times if it has multiple flagged inspections
    or multiple shipment records (split shipments).

    Args:
        db:        Active session.
        lot_code:  Limit to one lot code.
        date_from: Filter by lots.start_date ≥ date_from (AC3).
        date_to:   Filter by lots.start_date ≤ date_to (AC3).

    Returns:
        List[InspectionIssueRow], ordered by lot_id then inspection_date.

    Time complexity: O(k · s) where k = lots with flagged inspections,
        s = shipment records per lot.
    Space complexity: O(k · s).
    """
    query = (
        db.query(Lot)
        .options(
            selectinload(Lot.inspection_records),
            selectinload(Lot.shipping_records),
            selectinload(Lot.data_completeness),
        )
    )

    if lot_code:
        query = query.filter(Lot.lot_code == lot_code)
    if date_from:
        query = query.filter(Lot.start_date >= date_from)
    if date_to:
        query = query.filter(Lot.start_date <= date_to)

    lots = query.order_by(Lot.lot_id).all()

    rows: List[InspectionIssueRow] = []
    for lot in lots:
        flagged_inspections = [ir for ir in lot.inspection_records if ir.issue_flag]
        if not flagged_inspections:
            continue   # Lot has no flagged inspections — skip

        dc      = lot.data_completeness
        overall = dc.overall_completeness if dc else 0

        # For each flagged inspection, cross with each shipment (or None if no shipments)
        # This mirrors the LEFT JOIN in v_inspection_issue_shipping
        ship_records = lot.shipping_records or [None]   # [None] ensures at least one row per inspection

        for ir in flagged_inspections:
            for sr in ship_records:
                rows.append(InspectionIssueRow(
                    lot_id              = lot.lot_id,
                    lot_code            = lot.lot_code,
                    start_date          = lot.start_date,
                    inspection_date     = ir.inspection_date,
                    inspection_result   = ir.inspection_result,
                    inspector_notes     = ir.inspector_notes,
                    ship_date           = sr.ship_date           if sr else None,
                    shipment_status     = sr.shipment_status     if sr else None,
                    hold_reason         = sr.hold_reason         if sr else None,
                    customer            = sr.customer            if sr else None,
                    destination         = sr.destination         if sr else None,
                    overall_completeness= overall,
                ))

    return rows


def get_incomplete_lots(db: Session) -> List[IncompleteLotRow]:
    """
    Return all lots where overall_completeness < 100 (AC4, AC10).

    Implements `ops.v_incomplete_lots` (schema.sql §10c).

    Every new lot starts at 0% — the database trigger (or
    refresh_data_completeness in tests) initialises the row.  So this view
    always catches brand-new lots before any records are attached.

    The plain-English `completeness_note` helps analysts immediately
    understand what's missing before a meeting starts (AC10).

    Returns:
        List[IncompleteLotRow], ordered by overall_completeness ASC
        (most incomplete first) then lot_id.

    Time complexity: O(m) where m = lots with completeness < 100.
    Space complexity: O(m).
    """
    rows_db = (
        db.query(Lot, DataCompleteness)
        .join(DataCompleteness, DataCompleteness.lot_id == Lot.lot_id)
        .filter(DataCompleteness.overall_completeness < 100)
        .order_by(DataCompleteness.overall_completeness.asc(), Lot.lot_id.asc())
        .all()
    )

    result: List[IncompleteLotRow] = []
    for lot, dc in rows_db:
        # Build a human-readable description of exactly which data is missing
        note = _completeness_note(dc.has_production_data, dc.has_inspection_data, dc.has_shipping_data)

        result.append(IncompleteLotRow(
            lot_id               = lot.lot_id,
            lot_code             = lot.lot_code,
            start_date           = lot.start_date,
            end_date             = lot.end_date,
            has_production_data  = dc.has_production_data,
            has_inspection_data  = dc.has_inspection_data,
            has_shipping_data    = dc.has_shipping_data,
            overall_completeness = dc.overall_completeness,
            last_evaluated_at    = dc.last_evaluated_at,
            completeness_note    = note,
        ))

    return result


def _completeness_note(has_prod: bool, has_insp: bool, has_ship: bool) -> str:
    """
    Build a plain-English description of what data is missing.

    Mirrors the CASE expression in `ops.v_incomplete_lots`.

    Args:
        has_prod: True if production records exist.
        has_insp: True if inspection records exist.
        has_ship: True if shipping records exist.

    Returns:
        A human-readable string, e.g., "Missing inspection data".

    Time complexity: O(1) — fixed number of comparisons.
    """
    missing = []
    if not has_prod:
        missing.append("production")
    if not has_insp:
        missing.append("inspection")
    if not has_ship:
        missing.append("shipping")

    if len(missing) == 3:
        return "No data in any function"
    elif len(missing) == 2:
        return f"Missing {missing[0]} and {missing[1]}"
    elif len(missing) == 1:
        return f"Missing {missing[0]} data"
    else:
        return "Complete"


def get_line_issues(db: Session) -> List[LineIssueRow]:
    """
    Return issue counts and rates grouped by production line (AC5).

    Implements `ops.v_issues_by_production_line` (schema.sql §10d).

    Answers: "Which production lines had the most problems, and what kind?"
    Results are sorted by issue_runs DESC so the most problematic line
    appears first — optimised for quick answers in meetings (AC7).

    Strategy:
      1. Query all production records in one SELECT.
      2. Group in Python using a defaultdict of counters (O(p)).
      3. Sort by issue_runs DESC (O(k log k) where k = distinct lines, max 4).

    Args:
        db: Active SQLAlchemy session.

    Returns:
        List[LineIssueRow], ordered by issue_runs DESC (highest-issue line first).

    Time complexity: O(p) where p = total production records.
    Space complexity: O(k) where k = distinct production lines (max 4 here).
    """
    all_records = db.query(ProductionRecord).all()

    # Accumulate counters per line using defaultdict
    # key = production_line string; value = dict of counters
    counters: dict = defaultdict(lambda: {
        "total": 0, "issues": 0,
        "Tool wear": 0, "Sensor fault": 0, "Material shortage": 0,
        "Changeover delay": 0, "Quality hold": 0, "Operator training": 0,
    })

    for pr in all_records:
        c = counters[pr.production_line]
        c["total"] += 1                       # Count every run
        if pr.line_issue:
            c["issues"] += 1                  # Count flagged runs
        if pr.primary_issue and pr.primary_issue in c:
            c[pr.primary_issue] += 1           # Count by issue type

    # Convert aggregated dict to sorted list of schema objects
    # Sorted by issue_runs DESC (highest-issue line first — AC5)
    # O(k log k) sort where k = number of distinct lines (small constant ≤ 4)
    result: List[LineIssueRow] = []
    for line, c in sorted(counters.items(), key=lambda x: x[1]["issues"], reverse=True):
        total = c["total"]
        issues = c["issues"]
        # Division by zero guard: if no runs, rate is 0.0
        rate = round(issues / total * 100, 1) if total > 0 else 0.0

        result.append(LineIssueRow(
            production_line         = line,
            total_runs              = total,
            issue_runs              = issues,
            issue_rate_pct          = rate,
            tool_wear_count         = c["Tool wear"],
            sensor_fault_count      = c["Sensor fault"],
            material_shortage_count = c["Material shortage"],
            changeover_delay_count  = c["Changeover delay"],
            quality_hold_count      = c["Quality hold"],
            operator_training_count = c["Operator training"],
        ))

    return result
