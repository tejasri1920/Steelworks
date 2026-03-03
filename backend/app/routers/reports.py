# app/routers/reports.py
#
# HTTP endpoints for the four analytical reports.
#
# Endpoints:
#   GET /api/v1/reports/lot-summary          – aggregated one-row-per-lot view
#   GET /api/v1/reports/inspection-issues    – lots with flagged inspections + ship status
#   GET /api/v1/reports/incomplete-lots      – lots missing data in ≥1 function
#   GET /api/v1/reports/line-issues          – issue counts by production line
#
# AC coverage:
#   /lot-summary         → AC1, AC2, AC3, AC7, AC8, AC9
#   /inspection-issues   → AC5, AC6
#   /incomplete-lots     → AC4, AC10
#   /line-issues         → AC5

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import report_repo
from app.schemas.reports import LotSummaryRow, InspectionIssueRow, IncompleteLotRow, LineIssueRow

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/lot-summary",
    response_model=List[LotSummaryRow],
    summary="Meeting-ready lot summary (AC1, AC2, AC3, AC7, AC8)",
    description=(
        "Aggregates production, inspection, and shipping data into one row "
        "per lot.  Filter by lot_code or date range.  Replaces manual "
        "cross-referencing of three spreadsheets."
    ),
)
def lot_summary(
    lot_code:  Optional[str]  = Query(None, description="Exact lot code filter"),
    date_from: Optional[date] = Query(None, description="Lots with start_date ≥ this date"),
    date_to:   Optional[date] = Query(None, description="Lots with start_date ≤ this date"),
    db:        Session        = Depends(get_db),
) -> List[LotSummaryRow]:
    """
    Primary dashboard report — one row per lot covering all functions.

    This is the endpoint the frontend Dashboard page calls first.
    The response contains enough information to answer the most common
    operational questions without a follow-up query (AC7):
      - How many units were produced?
      - Were there any line or inspection issues?
      - Has the lot shipped?
      - Is the data complete?

    Returns HTTP 200 with a (possibly empty) list ordered by lot_id (AC9).
    """
    return report_repo.get_lot_summary(
        db=db,
        lot_code=lot_code,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/inspection-issues",
    response_model=List[InspectionIssueRow],
    summary="Lots with inspection issues and their shipping status (AC5, AC6)",
    description=(
        "Returns every lot with at least one flagged inspection, joined to "
        "its shipping record(s).  NULL ship_date means the lot has not yet "
        "been dispatched.  Answers: 'Have problematic lots already shipped?'"
    ),
)
def inspection_issues(
    lot_code:  Optional[str]  = Query(None, description="Exact lot code filter"),
    date_from: Optional[date] = Query(None, description="Lots with start_date ≥ this date"),
    date_to:   Optional[date] = Query(None, description="Lots with start_date ≤ this date"),
    db:        Session        = Depends(get_db),
) -> List[InspectionIssueRow]:
    """
    Inspection-issue × shipping-status cross-view.

    A lot appears here only if it has at least one InspectionRecord with
    issue_flag = True.  Its shipping records are LEFT-JOINed so lots with
    issues but no shipment still appear (ship_date = None) — the gap is
    visible (AC4).
    """
    return report_repo.get_inspection_issue_shipping(
        db=db,
        lot_code=lot_code,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/incomplete-lots",
    response_model=List[IncompleteLotRow],
    summary="Lots missing data from one or more functions (AC4, AC10)",
    description=(
        "Returns every lot with overall_completeness < 100%, sorted from "
        "most to least incomplete.  Each row includes a plain-English note "
        "explaining what is missing so analysts know before a meeting starts."
    ),
)
def incomplete_lots(
    db: Session = Depends(get_db),
) -> List[IncompleteLotRow]:
    """
    Data-quality view — highlights gaps before a meeting.

    Sorted by overall_completeness ASC so the most incomplete lots appear
    first.  The `completeness_note` field contains a plain-English message
    such as "Missing inspection and shipping" (AC10).
    """
    return report_repo.get_incomplete_lots(db=db)


@router.get(
    "/line-issues",
    response_model=List[LineIssueRow],
    summary="Issue counts and rates by production line (AC5)",
    description=(
        "Groups all production records by line and counts how many runs "
        "had issues, broken down by issue type.  Sorted by issue_runs DESC "
        "so the most problematic line appears first."
    ),
)
def line_issues(
    db: Session = Depends(get_db),
) -> List[LineIssueRow]:
    """
    Issue-by-line breakdown.

    Answers AC5: "Which production lines had the most issues, and what kind?"
    Sorted by issue_runs descending so the highest-problem line is on top.
    """
    return report_repo.get_line_issues(db=db)
