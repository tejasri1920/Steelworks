// src/components/LotSummaryTable.tsx
//
// The primary table component for the Dashboard — one row per lot.
// Covers AC1 (all functions shown together), AC2 (aligned by lot ID),
// AC4 (missing data visible), AC7 (meeting-ready), AC8 (no spreadsheets).
//
// Columns: Lot Code | Start Date | Production | Inspection | Shipping | Completeness
// Clicking a lot code navigates to LotDetailPage for the full drill-down.

import { useNavigate } from 'react-router-dom'
import type { LotSummaryRow } from '../types'
import CompletenessIndicator from './CompletenessIndicator'
import MissingDataBadge from './MissingDataBadge'

interface Props {
  rows:     LotSummaryRow[];
  isLoading: boolean;
  error?:   string | null;
}

/**
 * Meeting-ready lot summary table (AC7, AC8).
 *
 * Each row aggregates all three operational functions for one lot.
 * Color-coded badges draw attention to issues and incomplete data.
 *
 * Navigation: clicking a lot_code link navigates to /lots/{lot_code}.
 *
 * @param rows      Array of LotSummaryRow from the /reports/lot-summary endpoint.
 * @param isLoading Show skeleton state while data loads.
 * @param error     Error message to display if the fetch failed.
 */
export default function LotSummaryTable({ rows, isLoading, error }: Props) {
  const navigate = useNavigate()

  if (isLoading) return <TableSkeleton />
  if (error)     return <ErrorBanner message={error} />
  if (rows.length === 0) return <EmptyState />

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      {/* Result count badge */}
      <div className="px-4 py-2 border-b border-gray-100 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          {rows.length} lot{rows.length !== 1 ? 's' : ''} found
        </span>
        <span className="text-xs text-gray-400">Click a lot code for details</span>
      </div>

      {/* Horizontal scroll for narrow screens (common in factory environments) */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3 text-left">Lot Code</th>
              <th className="px-4 py-3 text-left">Start Date</th>
              {/* Production columns */}
              <th className="px-4 py-3 text-right">Runs</th>
              <th className="px-4 py-3 text-right">Units Produced</th>
              <th className="px-4 py-3 text-right">Attainment %</th>
              <th className="px-4 py-3 text-center">Line Issues</th>
              {/* Inspection columns */}
              <th className="px-4 py-3 text-center">Insp. Issues</th>
              {/* Shipping columns */}
              <th className="px-4 py-3 text-center">Shipments</th>
              <th className="px-4 py-3 text-center">Blocked?</th>
              {/* Completeness */}
              <th className="px-4 py-3 text-center">Data %</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr
                key={row.lot_id}
                className="hover:bg-slate-50 transition-colors"
              >
                {/* Lot code — clickable link to detail page (AC2, AC8) */}
                <td className="px-4 py-3">
                  <button
                    onClick={() => navigate(`/lots/${row.lot_code}`)}
                    className="font-mono text-blue-700 hover:underline text-left"
                    title="Click to view full lot detail"
                  >
                    {row.lot_code}
                  </button>
                </td>

                <td className="px-4 py-3 text-gray-600">
                  {new Date(row.start_date).toLocaleDateString()}
                </td>

                {/* Production — AC1: production data shown in same row */}
                <td className="px-4 py-3 text-right">
                  {row.has_production_data ? row.production_run_count : <MissingDataBadge value={null} />}
                </td>
                <td className="px-4 py-3 text-right">
                  <MissingDataBadge
                    value={row.total_units_produced}
                    format={(v) => v.toLocaleString()}
                  />
                </td>
                <td className="px-4 py-3 text-right">
                  <MissingDataBadge
                    value={row.attainment_pct}
                    format={(v) => `${v}%`}
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  {/* Red badge if any line issue, otherwise green check (AC5) */}
                  <IssueBadge
                    count={row.production_issue_count}
                    hasData={row.has_production_data}
                  />
                </td>

                {/* Inspection — AC1 */}
                <td className="px-4 py-3 text-center">
                  <IssueBadge
                    count={row.inspection_issue_count}
                    hasData={row.has_inspection_data}
                  />
                </td>

                {/* Shipping — AC1 */}
                <td className="px-4 py-3 text-center">
                  {row.has_shipping_data ? (
                    <span className="text-gray-700">{row.shipment_count}</span>
                  ) : (
                    <MissingDataBadge value={null} />
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {/* AC6: clearly show if any shipment is blocked */}
                  {row.has_shipping_data
                    ? row.any_shipment_blocked
                      ? <span className="text-xs font-bold text-orange-600 bg-orange-50 px-2 py-0.5 rounded border border-orange-200">BLOCKED</span>
                      : <span className="text-xs text-green-600">✓ Clear</span>
                    : <MissingDataBadge value={null} />
                  }
                </td>

                {/* Completeness — AC4, AC10 */}
                <td className="px-4 py-3">
                  <CompletenessIndicator
                    score={row.overall_completeness}
                    hasProduction={row.has_production_data}
                    hasInspection={row.has_inspection_data}
                    hasShipping={row.has_shipping_data}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Helper sub-components ─────────────────────────────────────────────────────

/** Red badge with issue count, or green check if zero issues, or N/A if no data. */
function IssueBadge({ count, hasData }: { count: number; hasData: boolean }) {
  if (!hasData) return <MissingDataBadge value={null} />
  if (count === 0) return <span className="text-xs text-green-600">✓</span>
  return (
    <span className="text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded">
      {count}
    </span>
  )
}

/** Loading skeleton while data is being fetched. */
function TableSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-3">
      <div className="text-sm text-gray-500">Loading data…</div>
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
      ))}
    </div>
  )
}

/** Error banner shown when the API request fails. */
function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
      <strong>Error loading data:</strong> {message}
    </div>
  )
}

/** Shown when the filter returns no results. */
function EmptyState() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-400">
      <div className="text-3xl mb-2">🔍</div>
      <div className="font-medium">No lots found for the selected filters.</div>
      <div className="text-sm mt-1">Try widening the date range or clearing the lot code.</div>
    </div>
  )
}
