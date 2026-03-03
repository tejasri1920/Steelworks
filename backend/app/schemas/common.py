# app/schemas/common.py
#
# Shared Pydantic schemas used across multiple endpoints.
#
# Pydantic schemas serve two purposes:
#   1. Validation: reject invalid request bodies or parameters before they
#      reach business logic.
#   2. Serialization: convert SQLAlchemy ORM objects to JSON-safe dicts for
#      the HTTP response.  FastAPI automatically calls `.model_dump()` on
#      any Pydantic model returned from a route handler.
#
# `model_config = ConfigDict(from_attributes=True)` tells Pydantic to read
# values from SQLAlchemy ORM object attributes (not just dict keys), which
# lets us do `LotSchema.model_validate(orm_lot)` directly.

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date


class ErrorDetail(BaseModel):
    """Standard error response body returned by all 4xx/5xx handlers."""
    detail: str


class HealthResponse(BaseModel):
    """Response body for GET /health — tells clients the API is alive."""
    status: str      # "ok"
    version: str     # Application version string


class DateRangeParams(BaseModel):
    """
    Reusable model for date-range query parameters.

    Both fields are optional so the caller can filter by:
      - Neither (all records)
      - date_from only (everything on or after that date)
      - date_to only (everything on or before that date)
      - Both (a closed range)
    """
    date_from: Optional[date] = None
    date_to:   Optional[date] = None
