# Steelworks Operations Analytics

> Unified Production · Inspection · Shipping dashboard — aligned by Lot ID.
> Answer meeting questions in seconds. No spreadsheet juggling required.

---

## Table of Contents

1. [Project Description](#1-project-description)
2. [How to Build & Run](#2-how-to-build--run)
   - [Option A — Docker (recommended)](#option-a--docker-recommended)
   - [Option B — Local development (no Docker)](#option-b--local-development-no-docker)
3. [Usage Examples](#3-usage-examples)
   - [Web UI walkthrough](#web-ui-walkthrough)
   - [API examples (curl)](#api-examples-curl)
4. [How to Run Tests](#4-how-to-run-tests)
5. [Project Structure](#5-project-structure)
6. [API Reference](#6-api-reference)
7. [AC → Test Coverage Map](#7-ac--test-coverage-map)
8. [Configuration Checklist](#8-configuration-checklist)

---

## 1. Project Description

### The problem

Operations analysts at Steelworks track lots (production batches) across three independent spreadsheets — one for Production, one for Inspection, one for Shipping. Answering a simple meeting question like *"Did Lot 112 pass inspection before it shipped?"* means opening and cross-referencing three files by hand.

### What this app does

**Steelworks Operations Analytics** is a read-only web dashboard that pulls all three data sources into a single PostgreSQL database and presents them in one unified, filterable view:

| What you need | How the app provides it |
|---|---|
| See all functions for a lot | One API call returns production + inspection + shipping together |
| Filter by lot code | Exact match search — `LOT-20260112-001` |
| Filter by date range | `date_from` / `date_to` on lot start date |
| Spot data gaps before a meeting | Completeness % badge (0 / 33 / 67 / 100%) with plain-English notes |
| Find which line had the most issues | Line Issues tab — sorted by issue count, broken down by cause |
| Know if a flagged lot already shipped | Inspection Issues tab — shows shipment status alongside every flagged inspection |

### Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · React Query |
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2 · Poetry |
| Database | PostgreSQL 16 (`ops` schema — triggers, views, indexes) |
| Container | Docker · Docker Compose · Nginx |

Architecture: **modular monolith** with a layered backend (Presentation → Business Logic → Data Access). See [docs/architecture_decision_records.md](docs/architecture_decision_records.md) for the design rationale.

---

## 2. How to Build & Run

### Option A — Docker (recommended)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / macOS / Linux)

> **Windows setup (one-time):**
> 1. Download and install Docker Desktop from the link above — accept the WSL 2 prompt.
> 2. Launch **Docker Desktop** from the Start menu and wait until the system-tray whale icon stops animating ("Docker Desktop is running").
> 3. Open a **new** terminal — the `docker` command is only available in terminals opened after Docker is running.

```bash
# 1. Copy the environment template
cp .env.example .env          # macOS / Linux / Git Bash / PowerShell
# copy .env.example .env      # Windows Command Prompt (cmd.exe)

# 2. Open .env and set a real database password
#    POSTGRES_PASSWORD=change_me_in_prod   ← change this line

# 3. Build and start all three containers (db + backend + frontend)
#    First run takes ~2 minutes while images download and build.
docker compose up --build

# 4. Visit the app
#    Dashboard:  http://localhost:3000
#    API docs:   http://localhost:8000/docs   (Swagger UI, try endpoints live)
#    Raw API:    http://localhost:8000/api/v1/lots
```

**Common Docker commands:**

```bash
# Stop containers (data is preserved)
docker compose down

# Stop and delete all data (full reset)
docker compose down -v

# Rebuild after changing source code
docker compose up --build

# View logs from a specific service
docker compose logs -f backend
docker compose logs -f db
```

---

### Option B — Local development (no Docker)

Run backend and frontend in separate terminals. You still need PostgreSQL installed locally or accessible remotely.

#### Terminal 1 — Database setup

```bash
# Create the database and apply the schema
psql -U postgres -c "CREATE DATABASE steelworks_ops;"
psql -U postgres -d steelworks_ops -f db/schema.sql    # Creates all tables, triggers, views
psql -U postgres -d steelworks_ops -f db/seed.sql      # Loads ~80 sample lots
```

> **Windows note:** `createdb` is not on the PATH by default. Use the `psql -c "CREATE DATABASE ..."` form above instead, or add `C:\Program Files\PostgreSQL\16\bin` to your system PATH and restart your terminal.
>
> **macOS / Linux note:** if your PostgreSQL superuser is not `postgres`, replace `-U postgres` with your username, or omit `-U` entirely to use the OS login user.

#### Terminal 2 — Backend (FastAPI)

```bash
cd backend

# Install Poetry (first time only)
curl -sSL https://install.python-poetry.org | python3 -

# Install all Python dependencies into a virtual environment
poetry install

# Configure environment
cp ../.env.example .env          # macOS / Linux / Git Bash / PowerShell
# copy .env.example .env         # Windows Command Prompt (cmd.exe)
# Edit .env: set DATABASE_URL=postgresql://your_user:password@localhost:5432/steelworks_ops

# Start the development server with hot-reload
poetry run uvicorn app.main:app --reload --port 8000
```

The backend is ready at **http://localhost:8000**. Interactive docs at **http://localhost:8000/docs**.

#### Terminal 3 — Frontend (React / Vite)

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite dev server
npm run dev
```

The frontend is ready at **http://localhost:5173**. Vite automatically proxies `/api/*` to `localhost:8000` so no CORS setup is needed in dev.

#### Build the frontend for production

```bash
cd frontend
npm run build        # Outputs compiled assets to frontend/dist/
npm run preview      # Preview the production build locally at localhost:4173
```

---

## 3. Usage Examples

### Web UI walkthrough

#### Scenario A — "What happened to Lot LOT-20260112-001?"

1. Open **http://localhost:3000**
2. In the **Lot Code** search box, type `LOT-20260112-001` and click **Apply**
3. The **Lot Summary** table shows one row with:
   - Production run count, units produced, attainment %
   - Whether any inspection issues were flagged
   - Shipment status and whether anything is blocked
   - A completeness badge (0 / 33 / 67 / 100%)
4. Click the lot code link → opens the **Lot Detail** page with full production, inspection, and shipping records side by side

#### Scenario B — "Which production line had the most issues in January?"

1. Set **Start Date (From)** = `2026-01-01` and **End Date (To)** = `2026-01-31`, click **Apply**
2. Click the **Line Issues** tab
3. Lines are sorted by issue count descending — the worst line is at the top
4. Columns show a breakdown by cause: Tool Wear · Sensor · Material · Changeover · Quality · Training

#### Scenario C — "Have any flagged lots shipped before being cleared?"

1. Click the **Inspection Issues** tab (filter dates if needed)
2. The table shows every lot with a flagged inspection alongside its shipping status
3. A red **Shipped** badge = the lot has already left the facility
4. An orange **On Hold** badge = the lot is held, with the hold reason shown in the next column
5. *Not dispatched* in the Status column = the lot has not been shipped at all

#### Scenario D — "What data gaps do we have going into this meeting?"

1. Click the **Incomplete Lots** tab
2. Results are sorted from most incomplete (0%) to least (67%)
3. The **What's Missing** column uses plain English: *"Missing inspection data"*, *"No data in any function"*
4. The **Last Evaluated** column shows when the completeness score was computed

---

### API examples (curl)

All examples below assume the backend is running at `http://localhost:8000`.
Open **http://localhost:8000/docs** to try every endpoint interactively in a browser.

#### Get all lots (first 100, ordered by lot_id)

```bash
curl http://localhost:8000/api/v1/lots
```

#### Look up a specific lot by code

```bash
curl http://localhost:8000/api/v1/lots/LOT-20260112-001
```

Sample response:

```json
{
  "lot_id": 58,
  "lot_code": "LOT-20260112-001",
  "start_date": "2026-01-12",
  "end_date": null,
  "production_records": [
    {
      "production_id": 4,
      "production_date": "2026-01-12",
      "production_line": "Line 1",
      "part_number": "SW-8091-A",
      "units_planned": 400,
      "quantity_produced": 382,
      "downtime_min": 44,
      "shift": "Swing",
      "line_issue": true,
      "primary_issue": null,
      "supervisor_notes": null
    }
  ],
  "inspection_records": [],
  "shipping_records": [
    {
      "shipping_id": 2,
      "ship_date": "2026-01-29",
      "shipment_status": "Shipped",
      "destination": "MI",
      "customer": "Prairie Pumps",
      "qty_shipped": 61,
      "hold_reason": null
    }
  ],
  "completeness": {
    "has_production_data": true,
    "has_inspection_data": false,
    "has_shipping_data": true,
    "overall_completeness": 67,
    "last_evaluated_at": "2026-02-24T10:00:00Z"
  }
}
```

#### Filter lots by date range

```bash
# All lots that started in January 2026
curl "http://localhost:8000/api/v1/lots?date_from=2026-01-01&date_to=2026-01-31"
```

#### Meeting-ready one-row-per-lot summary

```bash
# Summary for a specific date range
curl "http://localhost:8000/api/v1/reports/lot-summary?date_from=2026-01-10&date_to=2026-01-20"

# Summary for a single lot
curl "http://localhost:8000/api/v1/reports/lot-summary?lot_code=LOT-20260112-001"
```

#### Which lines had the most issues?

```bash
curl http://localhost:8000/api/v1/reports/line-issues
```

Sample response (sorted by issue_runs descending):

```json
[
  {
    "production_line": "Line 1",
    "total_runs": 30,
    "issue_runs": 18,
    "issue_rate_pct": 60.0,
    "tool_wear_count": 4,
    "sensor_fault_count": 6,
    "material_shortage_count": 3,
    "changeover_delay_count": 3,
    "quality_hold_count": 2,
    "operator_training_count": 0
  }
]
```

#### Lots with flagged inspections + their shipping status

```bash
curl http://localhost:8000/api/v1/reports/inspection-issues
```

#### Lots missing data from one or more functions

```bash
curl http://localhost:8000/api/v1/reports/incomplete-lots
```

Sample response:

```json
[
  {
    "lot_id": 4,
    "lot_code": "LOT-20260104-001",
    "overall_completeness": 0,
    "has_production_data": false,
    "has_inspection_data": false,
    "has_shipping_data": false,
    "completeness_note": "No data in any function",
    "last_evaluated_at": "2026-02-24T10:00:00Z"
  },
  {
    "lot_id": 12,
    "lot_code": "LOT-20260112-001",
    "overall_completeness": 67,
    "has_production_data": true,
    "has_inspection_data": false,
    "has_shipping_data": true,
    "completeness_note": "Missing inspection data",
    "last_evaluated_at": "2026-02-24T10:00:00Z"
  }
]
```

---

## 4. How to Run Tests

Tests use an **SQLite in-memory database** — no PostgreSQL or Docker required. The test suite sets `TESTING=true` automatically, which switches the engine to SQLite and disables PostgreSQL-specific features.

```bash
cd backend

# Install dependencies (if not already done)
poetry install

# Run the full test suite
poetry run pytest

# Run with verbose output (shows each test name and pass/fail)
poetry run pytest -v

# Run with a coverage report
#   --cov=app            measures coverage across the entire app/ package
#   --cov-report=term-missing  prints which lines are NOT covered
poetry run pytest --cov=app --cov-report=term-missing

# Run only the lot-endpoint tests
poetry run pytest tests/test_lots.py -v

# Run only the report-endpoint tests
poetry run pytest tests/test_reports.py -v

# Run a single test class
poetry run pytest tests/test_reports.py::TestInspectionIssues -v

# Run a single specific test
poetry run pytest tests/test_reports.py::TestInspectionIssues::test_on_hold_lot_shows_status -v

# Stop on the first failure (useful when debugging)
poetry run pytest -x
```

### What the tests cover

The suite contains **35 tests** across two files:

| File | Test classes | Focus |
|---|---|---|
| `tests/test_lots.py` | `TestLotDetail`, `TestLotList`, `TestConsistency` | Lot endpoints, filtering, 404 handling |
| `tests/test_reports.py` | `TestLotSummary`, `TestInspectionIssues`, `TestIncompleteLots`, `TestLineIssues`, `TestConsistency` | All four report endpoints |

Every test uses a **shared 4-lot fixture** defined in `tests/conftest.py`:

| Lot | Data present | Purpose |
|---|---|---|
| `LOT-A` | Production ✓ · Inspection ✓ · Shipping ✓ | Complete lot — baseline |
| `LOT-B` | Production ✓ · Inspection ✗ · Shipping ✓ | Missing one function (67%) |
| `LOT-C` | Production ✓ · Inspection ✓ (flagged) · Shipping ✓ (On Hold) | Issue + blocked shipment |
| `LOT-D` | None | Brand-new lot, 0% completeness |

### Expected output (all tests passing)

```
============================= test session starts ==============================
collected 35 items

tests/test_lots.py::TestLotDetail::test_lot_detail_has_all_three_functions PASSED
tests/test_lots.py::TestLotDetail::test_lot_detail_aligns_by_lot_id PASSED
tests/test_lots.py::TestLotDetail::test_lot_detail_shows_empty_lists_for_missing_data PASSED
...
tests/test_reports.py::TestConsistency::test_line_issues_consistent_on_repeat PASSED

============================== 35 passed in 1.2s ===============================
```

---

## 5. Project Structure

```
steelworks/
├── docker-compose.yml          # Orchestrates db + backend + frontend containers
├── .env.example                # Template — copy to .env and fill in secrets
│
├── db/
│   ├── schema.sql              # PostgreSQL DDL: tables, indexes, triggers, 4 views
│   └── seed.sql                # ~80 sample lots with production & shipping records
│
├── backend/
│   ├── Dockerfile              # Multi-stage: Poetry builder → slim Python runtime
│   ├── pyproject.toml          # Poetry manifest (dependencies + test config)
│   │
│   ├── app/
│   │   ├── main.py             # FastAPI app: CORS, router registration, /health
│   │   ├── config.py           # Typed settings (reads .env via pydantic-settings)
│   │   ├── database.py         # SQLAlchemy engine, SessionLocal, get_db dependency
│   │   │
│   │   ├── models/             # SQLAlchemy ORM table definitions
│   │   │   ├── lot.py          # lots table + relationships
│   │   │   ├── production.py   # production_records table
│   │   │   ├── inspection.py   # inspection_records table
│   │   │   ├── shipping.py     # shipping_records table
│   │   │   └── data_completeness.py  # data_completeness table
│   │   │
│   │   ├── schemas/            # Pydantic response schemas (validation + serialization)
│   │   │   ├── common.py       # Shared types (ErrorDetail, DateRangeParams)
│   │   │   ├── lot.py          # LotSummary, LotDetail, nested child schemas
│   │   │   └── reports.py      # LotSummaryRow, InspectionIssueRow, LineIssueRow, …
│   │   │
│   │   ├── repositories/       # All database queries live here (no SQL in routers)
│   │   │   ├── lot_repo.py     # get_lots(), get_lot_by_code(), refresh_data_completeness()
│   │   │   └── report_repo.py  # get_lot_summary(), get_inspection_issue_shipping(), …
│   │   │
│   │   └── routers/            # HTTP route handlers (thin — delegate to repositories)
│   │       ├── lots.py         # GET /api/v1/lots  ·  GET /api/v1/lots/{lot_code}
│   │       └── reports.py      # GET /api/v1/reports/*
│   │
│   └── tests/
│       ├── conftest.py         # SQLite engine, session fixture, 4-lot seeded dataset
│       ├── test_lots.py        # 17 tests — AC1,2,3,4,8,9,10
│       └── test_reports.py     # 18 tests — AC1–10 (all four report endpoints)
│
├── frontend/
│   ├── Dockerfile              # Multi-stage: Node builder → Nginx static server
│   ├── nginx.conf              # SPA fallback routing + /api/* proxy to backend
│   ├── package.json
│   ├── vite.config.ts          # Dev proxy: /api → localhost:8000
│   ├── tailwind.config.js
│   │
│   └── src/
│       ├── main.tsx            # React root: QueryClientProvider + BrowserRouter
│       ├── App.tsx             # Route definitions (/ and /lots/:lot_code)
│       ├── index.css           # Tailwind base + global styles
│       │
│       ├── types/index.ts      # TypeScript interfaces mirroring backend schemas
│       ├── api/client.ts       # Axios functions for every backend endpoint
│       │
│       ├── components/
│       │   ├── Navbar.tsx                # Persistent header with brand + nav links
│       │   ├── DateRangeFilter.tsx       # Lot code + date range filter bar (AC2, AC3)
│       │   ├── CompletenessIndicator.tsx # %-badge + P/I/S coverage dots (AC4, AC10)
│       │   ├── MissingDataBadge.tsx      # "N/A" label when a field is null (AC4)
│       │   ├── LotSummaryTable.tsx       # Main summary table (AC1,2,7,8)
│       │   ├── InspectionIssuesTable.tsx # Flagged lots + ship status (AC5,6)
│       │   ├── LineIssuesTable.tsx       # Issue rate bar chart per line (AC5)
│       │   └── IncompleteLotsTable.tsx   # Sorted incomplete lots (AC4,10)
│       │
│       └── pages/
│           ├── DashboardPage.tsx         # Tabbed main view (all four reports)
│           └── LotDetailPage.tsx         # Full drill-down for one lot (AC1,8)
│
└── docs/
    ├── architecture_decision_records.md  # Why modular monolith?
    ├── tech_stack_decision_records.md    # Why FastAPI + React + PostgreSQL?
    ├── assumptions_scope.md              # What's in and out of scope
    └── data_design.md                   # ERD + field descriptions
```

---

## 6. API Reference

Interactive docs (try endpoints live): **http://localhost:8000/docs**

### Endpoints

| Method | Path | Description | ACs |
|--------|------|-------------|-----|
| `GET` | `/health` | Liveness probe — returns `{"status":"ok"}` | — |
| `GET` | `/api/v1/lots` | Paginated lot list with optional filters | AC2, AC3 |
| `GET` | `/api/v1/lots/{lot_code}` | Full lot + all child records | AC1, AC4, AC8 |
| `GET` | `/api/v1/reports/lot-summary` | One-row-per-lot meeting summary | AC1,2,3,7,8,9 |
| `GET` | `/api/v1/reports/inspection-issues` | Flagged inspections + ship status | AC5, AC6 |
| `GET` | `/api/v1/reports/incomplete-lots` | Lots with data gaps, sorted worst-first | AC4, AC10 |
| `GET` | `/api/v1/reports/line-issues` | Issue counts ranked by production line | AC5 |

### Query parameters (filterable endpoints)

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `lot_code` | string | `LOT-20260112-001` | Exact lot code match (case-sensitive) |
| `date_from` | date | `2026-01-01` | Include lots with `start_date ≥` this value |
| `date_to` | date | `2026-01-31` | Include lots with `start_date ≤` this value |
| `skip` | int | `0` | Pagination offset (lots list only) |
| `limit` | int | `100` | Page size, max 500 (lots list only) |

---

## 7. AC → Test Coverage Map

Every acceptance criterion is covered by at least one automated test.

| AC | Description | Test file → test name(s) |
|----|-------------|--------------------------|
| **AC1** | All functions shown together | `test_lots.py` → `TestLotDetail::test_lot_detail_has_all_three_functions` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_includes_all_functions` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_combines_all_functions` |
| **AC2** | Aligned by lot ID | `test_lots.py` → `TestLotDetail::test_lot_detail_aligns_by_lot_id` |
| | | `test_lots.py` → `TestLotList::test_list_lots_filter_by_lot_code` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_aligns_by_lot_id` |
| **AC3** | Date-range filtering | `test_lots.py` → `TestLotList::test_list_lots_filter_by_date_from` |
| | | `test_lots.py` → `TestLotList::test_list_lots_filter_by_date_to` |
| | | `test_lots.py` → `TestLotList::test_list_lots_date_range_both_bounds` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_date_from_filter` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_date_to_filter` |
| | | `test_reports.py` → `TestInspectionIssues::test_inspection_issues_date_filter` |
| **AC4** | Missing data visible | `test_lots.py` → `TestLotDetail::test_lot_detail_shows_empty_lists_for_missing_data` |
| | | `test_lots.py` → `TestLotDetail::test_lot_detail_completeness_reflects_missing` |
| | | `test_lots.py` → `TestLotDetail::test_lot_detail_completeness_score_0` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_shows_missing_flags` |
| | | `test_reports.py` → `TestIncompleteLots::test_incomplete_lots_lists_missing` |
| | | `test_reports.py` → `TestIncompleteLots::test_lot_d_appears_with_zero_completeness` |
| **AC5** | Line issue identification | `test_reports.py` → `TestLineIssues::test_line_with_most_issues_is_first` |
| | | `test_reports.py` → `TestLineIssues::test_line_issue_rate_calculated_correctly` |
| | | `test_reports.py` → `TestLineIssues::test_line_issue_breakdown_by_type` |
| | | `test_reports.py` → `TestInspectionIssues::test_flagged_lots_appear_in_report` |
| **AC6** | Shipment status clarity | `test_reports.py` → `TestInspectionIssues::test_on_hold_lot_shows_status` |
| | | `test_reports.py` → `TestInspectionIssues::test_on_hold_lot_shows_hold_reason` |
| | | `test_reports.py` → `TestInspectionIssues::test_shipped_lot_shows_status` |
| | | `test_reports.py` → `TestInspectionIssues::test_unshipped_lot_shows_null_ship_date` |
| **AC7** | Meeting-ready summaries | `test_reports.py` → `TestLotSummary::test_lot_summary_is_one_row_per_lot` |
| **AC8** | No manual spreadsheets | `test_lots.py` → `TestLotDetail::test_lot_detail_has_all_three_functions` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_combines_all_functions` |
| **AC9** | Consistent results | `test_lots.py` → `TestConsistency::test_same_lot_query_returns_consistent_result` |
| | | `test_lots.py` → `TestConsistency::test_list_lots_consistent_on_repeat` |
| | | `test_reports.py` → `TestConsistency::test_lot_summary_consistent_on_repeat` |
| | | `test_reports.py` → `TestConsistency::test_inspection_issues_consistent_on_repeat` |
| | | `test_reports.py` → `TestConsistency::test_incomplete_lots_consistent_on_repeat` |
| | | `test_reports.py` → `TestConsistency::test_line_issues_consistent_on_repeat` |
| **AC10** | Completeness awareness | `test_lots.py` → `TestLotDetail::test_lot_detail_completeness_score_100` |
| | | `test_lots.py` → `TestLotDetail::test_lot_detail_completeness_score_0` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_completeness_score_67` |
| | | `test_reports.py` → `TestLotSummary::test_lot_summary_completeness_score_0` |
| | | `test_reports.py` → `TestIncompleteLots::test_completeness_note_for_missing_inspection` |
| | | `test_reports.py` → `TestIncompleteLots::test_completeness_note_for_no_data` |
| | | `test_reports.py` → `TestIncompleteLots::test_incomplete_lots_sorted_most_incomplete_first` |

---

## 8. Configuration Checklist

### Things to change before deploying

| File | Variable / location | What to set |
|------|---------------------|-------------|
| `.env` | `POSTGRES_PASSWORD` | A strong random password (never the example value) |
| `.env` | `ALLOWED_ORIGINS` | Your real frontend URL, e.g. `https://ops.yourcompany.com` |
| `.env` | `VITE_API_BASE_URL` | Your server's IP or domain, e.g. `https://api.yourcompany.com` |
| `backend/pyproject.toml` line 9 | `authors` | Your name and email address |

### Recommended production additions

| Topic | What to do |
|-------|------------|
| **Authentication** | Add OAuth2 / JWT middleware to FastAPI so only authorised users can view data |
| **HTTPS / TLS** | Place the Nginx container behind Caddy or Traefik with a free Let's Encrypt cert |
| **Database backups** | Schedule nightly `pg_dump` to S3 or another remote location and test restores |
| **Data ingestion** | Build an ETL script that reads new Production/Shipping spreadsheet exports and inserts rows into the `ops` schema |
| **Secrets** | Move `.env` secrets into Docker secrets, AWS Secrets Manager, or Azure Key Vault in production |
| **Monitoring** | Add a `/ready` endpoint that runs `SELECT 1` against the DB and hook it to your uptime checker |

---

*Built with [FastAPI](https://fastapi.tiangolo.com/) · [React](https://react.dev/) · [PostgreSQL](https://www.postgresql.org/)*
