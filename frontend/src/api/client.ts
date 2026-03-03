// src/api/client.ts
//
// Centralized API client built on axios.
//
// Why centralize this?
//   - One place to set the base URL and default headers.
//   - One place to add auth tokens or error interceptors in the future.
//   - All components use named functions instead of raw axios calls, so
//     changing the base URL or adding a token only requires one edit here.
//
// The base URL is read from the Vite environment variable VITE_API_BASE_URL.
// In development (npm run dev): the Vite proxy forwards /api/* to localhost:8000
//   so VITE_API_BASE_URL can be an empty string "" (same-origin).
// In Docker: set VITE_API_BASE_URL="" because Nginx handles the proxy.
// If running the frontend separately: set VITE_API_BASE_URL=http://your-server:8000

import axios from 'axios';
import type {
  LotSummary,
  LotDetail,
  LotSummaryRow,
  InspectionIssueRow,
  IncompleteLotRow,
  LineIssueRow,
  ReportFilters,
} from '../types';

// `import.meta.env` is how Vite exposes environment variables to browser code.
// Variables must be prefixed with VITE_ to be included in the client bundle
// (this prevents accidentally exposing server-side secrets).
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

/** Axios instance configured for the Steelworks backend. */
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,       // 30 s timeout — generous for large datasets
  headers: {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
  },
});


// ── Lot endpoints ──────────────────────────────────────────────────────────────

/**
 * Fetch a paginated list of lots.
 *
 * @param filters Optional lot_code / date_from / date_to filters.
 * @returns Array of LotSummary objects (lightweight, no child records).
 *
 * Corresponds to: GET /api/v1/lots
 */
export async function fetchLots(filters?: ReportFilters): Promise<LotSummary[]> {
  const { data } = await api.get<LotSummary[]>('/api/v1/lots', {
    params: filters,   // axios serializes the object as ?lot_code=...&date_from=...
  });
  return data;
}

/**
 * Fetch full detail for a single lot including all child records (AC1, AC8).
 *
 * @param lotCode The business lot code, e.g., "LOT-20260112-001".
 * @returns LotDetail with nested production, inspection, and shipping records.
 *
 * Corresponds to: GET /api/v1/lots/{lot_code}
 */
export async function fetchLotDetail(lotCode: string): Promise<LotDetail> {
  const { data } = await api.get<LotDetail>(`/api/v1/lots/${encodeURIComponent(lotCode)}`);
  return data;
}


// ── Report endpoints ───────────────────────────────────────────────────────────

/**
 * Fetch the meeting-ready lot summary report (AC1, AC2, AC7, AC8).
 * One row per lot aggregating all three functions.
 *
 * Corresponds to: GET /api/v1/reports/lot-summary
 */
export async function fetchLotSummary(filters?: ReportFilters): Promise<LotSummaryRow[]> {
  const { data } = await api.get<LotSummaryRow[]>('/api/v1/reports/lot-summary', {
    params: filters,
  });
  return data;
}

/**
 * Fetch lots with flagged inspections and their shipping status (AC5, AC6).
 *
 * Corresponds to: GET /api/v1/reports/inspection-issues
 */
export async function fetchInspectionIssues(filters?: ReportFilters): Promise<InspectionIssueRow[]> {
  const { data } = await api.get<InspectionIssueRow[]>('/api/v1/reports/inspection-issues', {
    params: filters,
  });
  return data;
}

/**
 * Fetch lots missing data from at least one function (AC4, AC10).
 *
 * Corresponds to: GET /api/v1/reports/incomplete-lots
 */
export async function fetchIncompleteLots(): Promise<IncompleteLotRow[]> {
  const { data } = await api.get<IncompleteLotRow[]>('/api/v1/reports/incomplete-lots');
  return data;
}

/**
 * Fetch issue counts grouped by production line (AC5).
 *
 * Corresponds to: GET /api/v1/reports/line-issues
 */
export async function fetchLineIssues(): Promise<LineIssueRow[]> {
  const { data } = await api.get<LineIssueRow[]>('/api/v1/reports/line-issues');
  return data;
}
