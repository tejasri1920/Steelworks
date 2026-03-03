# app/routers/lots.py
#
# HTTP endpoints for Lot resources.
#
# Endpoints:
#   GET /api/v1/lots            – paginated lot list with optional filters
#   GET /api/v1/lots/{lot_code} – single lot with all child records
#
# This router is "thin": it validates inputs, delegates to the repository,
# and converts ORM objects → Pydantic schemas.  No business logic lives here.
#
# AC coverage:
#   AC1, AC2, AC8 – GET /lots/{lot_code} returns all three functions together
#   AC3            – date_from / date_to filter on GET /lots
#   AC9            – deterministic ordering ensures consistent results

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import lot_repo
from app.schemas.lot import LotSummary, LotDetail, ProductionRecordSchema, InspectionRecordSchema, ShippingRecordSchema, CompletenessSchema

# APIRouter groups related endpoints under the same URL prefix.
# The prefix "/lots" is appended to whatever prefix is set in main.py.
router = APIRouter(prefix="/lots", tags=["Lots"])


@router.get(
    "",
    response_model=List[LotSummary],
    summary="List lots with optional filters",
    description=(
        "Returns a paginated list of lots. "
        "Filter by lot_code (exact match) or a date range on start_date. "
        "Supports AC2 (lot alignment) and AC3 (date filtering)."
    ),
)
def list_lots(
    lot_code:  Optional[str]  = Query(None, description="Exact lot code, e.g. LOT-20260112-001"),
    date_from: Optional[date] = Query(None, description="Include lots with start_date ≥ this date (YYYY-MM-DD)"),
    date_to:   Optional[date] = Query(None, description="Include lots with start_date ≤ this date (YYYY-MM-DD)"),
    skip:      int            = Query(0,    ge=0, description="Pagination: number of records to skip"),
    limit:     int            = Query(100,  ge=1, le=500, description="Pagination: max records to return"),
    db:        Session        = Depends(get_db),
) -> List[LotSummary]:
    """
    List lots matching the provided filters.

    Query parameters are all optional — omitting all returns the first `limit`
    lots in creation order (deterministic due to ORDER BY lot_id — AC9).

    Returns HTTP 200 with a (possibly empty) list.
    """
    lots = lot_repo.get_lots(
        db=db,
        lot_code=lot_code,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    # Convert ORM objects to Pydantic schemas.
    # model_validate reads ORM attributes because from_attributes=True.
    return [LotSummary.model_validate(lot) for lot in lots]


@router.get(
    "/{lot_code}",
    response_model=LotDetail,
    summary="Get full lot detail with all functions",
    description=(
        "Returns a single lot with all its production, inspection, and "
        "shipping records.  Replaces opening three spreadsheets (AC1, AC8). "
        "Records align by lot_id (AC2).  Missing functions show as empty "
        "lists with has_*_data = false (AC4)."
    ),
)
def get_lot(
    lot_code: str,
    db:       Session = Depends(get_db),
) -> LotDetail:
    """
    Fetch a single lot with eagerly-loaded child records.

    Path parameter:
        lot_code: Business lot code (e.g., 'LOT-20260112-001').

    Returns:
        HTTP 200 LotDetail if the lot exists.
        HTTP 404 if no lot with that code is found.

    The `completeness` field tells the caller which functions have data and
    the overall coverage score (AC4, AC10).
    """
    lot = lot_repo.get_lot_by_code(db, lot_code)

    if lot is None:
        # Return 404 with a descriptive message so the frontend can show
        # "Lot not found" instead of a generic error.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lot '{lot_code}' not found.",
        )

    # Build the nested response manually because LotDetail contains nested
    # lists of child schemas — model_validate handles this for us.
    return LotDetail(
        lot_id             = lot.lot_id,
        lot_code           = lot.lot_code,
        start_date         = lot.start_date,
        end_date           = lot.end_date,
        production_records = [ProductionRecordSchema.model_validate(pr) for pr in lot.production_records],
        inspection_records = [InspectionRecordSchema.model_validate(ir) for ir in lot.inspection_records],
        shipping_records   = [ShippingRecordSchema.model_validate(sr)   for sr in lot.shipping_records],
        completeness       = CompletenessSchema.model_validate(lot.data_completeness)
                             if lot.data_completeness else None,
    )
