# app/main.py
#
# Entry point for the FastAPI application.
#
# This file is the top-level "app factory" that:
#   1. Creates the FastAPI application instance
#   2. Adds middleware (CORS for the React frontend)
#   3. Registers routers (lots, reports)
#   4. Defines a /health endpoint for container readiness checks
#
# FastAPI automatically generates interactive API documentation at:
#   http://localhost:8000/docs      (Swagger UI — try endpoints in a browser)
#   http://localhost:8000/redoc     (ReDoc — cleaner read-only view)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import lots as lots_router
from app.routers import reports as reports_router

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
# `title` and `description` appear in the Swagger UI and OpenAPI spec.
# `version` should match pyproject.toml's version field.
app = FastAPI(
    title="Steelworks Operations Analytics API",
    description=(
        "Unifies Production, Inspection, and Shipping data by Lot ID. "
        "Provides meeting-ready summaries and data-completeness visibility "
        "so analysts no longer need to open multiple spreadsheets."
    ),
    version="0.1.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) is a browser security mechanism.
# Without this middleware, the React frontend (running on :5173 or :3000)
# would be blocked from calling the API (on :8000) because they are on
# different origins (different ports = different origins).
#
# `allow_origins` is read from the ALLOWED_ORIGINS environment variable
# (default: http://localhost:5173,http://localhost:3000).
# In production, replace with the actual deployed frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # Which frontends may call us
    allow_credentials=True,                        # Allow cookies (future auth)
    allow_methods=["GET"],                         # Read-only API — only GET needed
    allow_headers=["*"],                           # Any request header is fine
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
# All routes live under /api/v1/ so the API can be versioned later.
# Adding v2 endpoints wouldn't break existing clients using /api/v1/.
app.include_router(lots_router.router,    prefix="/api/v1")
app.include_router(reports_router.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness check",
    description="Returns {status: ok} when the API is running. Used by Docker health checks.",
)
def health():
    """
    Simple liveness probe.

    Docker Compose (and load balancers like AWS ALB) use this endpoint to
    decide whether the container is healthy and should receive traffic.

    Returns HTTP 200 with {"status": "ok"} when the API is running.
    No database call is made — this checks application liveness only.
    For a full readiness check (including DB connectivity), a separate
    /ready endpoint with a simple SELECT 1 query could be added later.
    """
    return {"status": "ok", "version": "0.1.0"}
