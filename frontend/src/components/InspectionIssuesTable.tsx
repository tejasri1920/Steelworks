// src/components/InspectionIssuesTable.tsx
//
// Table for the inspection-issues report (AC5, AC6).
// Shows every lot with a flagged inspection alongside its shipping status.
// Makes it immediately clear whether problematic lots have shipped (AC6).

import type { InspectionIssueRow } from '../types'
import MissingDataBadge from './MissingDataBadge'

interface Props {
  rows:      InspectionIssueRow[];
  isLoading: boolean;
  error?:    string | null;
}

/**
 * Inspection-issues + shipping-status table (AC5, AC6).
 *
 * Key column: `shipment_status` — answers "Has this problematic lot shipped?"
 *   - 'Shipped'     → danger (it left despite issues)
 *   - 'On Hold'     → warning (held back — good, but needs resolution)
 *   - null/undefined → not yet dispatched (AC4 missing data visibility)
 *   - 'Backordered' → pending
 */
export default function InspectionIssuesTable({ rows, isLoading, error }: Props) {
  if (isLoading) return <div className="text-sm text-gray-500 p-4">Loading…</div>
  if (error)     return <div className="text-red-600 text-sm p-4">{error}</div>
  if (rows.length === 0) return (
    <div className="bg-green-50 border border-green-200 rounded p-4 text-green-700 text-sm">
      ✓ No lots with flagged inspections found for the selected period.
    </div>
  )

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-100 text-sm text-gray-500">
        {rows.length} inspection issue{rows.length !== 1 ? 's' : ''} found
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3 text-left">Lot Code</th>
              <th className="px-4 py-3 text-left">Insp. Date</th>
              <th className="px-4 py-3 text-center">Result</th>
              <th className="px-4 py-3 text-left">Inspector Notes</th>
              <th className="px-4 py-3 text-left">Ship Date</th>
              <th className="px-4 py-3 text-center">Ship Status</th>
              <th className="px-4 py-3 text-left">Hold Reason</th>
              <th className="px-4 py-3 text-left">Customer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-blue-700">{row.lot_code}</td>
                <td className="px-4 py-3 text-gray-600">
                  {new Date(row.inspection_date).toLocaleDateString()}
                </td>

                {/* Inspection result colored badge */}
                <td className="px-4 py-3 text-center">
                  <InspectionResultBadge result={row.inspection_result} />
                </td>

                <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">
                  <MissingDataBadge value={row.inspector_notes} missingLabel="—" />
                </td>

                {/* Shipping columns — NULL means not yet shipped (AC4, AC6) */}
                <td className="px-4 py-3 text-gray-600">
                  <MissingDataBadge
                    value={row.ship_date}
                    format={(d) => new Date(d).toLocaleDateString()}
                    missingLabel="Not shipped"
                  />
                </td>

                <td className="px-4 py-3 text-center">
                  <ShipmentStatusBadge status={row.shipment_status} />
                </td>

                <td className="px-4 py-3 text-xs text-gray-600">
                  <MissingDataBadge value={row.hold_reason} missingLabel="—" />
                </td>

                <td className="px-4 py-3 text-gray-600">
                  <MissingDataBadge value={row.customer} missingLabel="—" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/** Color-coded inspection result badge. */
function InspectionResultBadge({ result }: { result: string }) {
  const classes =
    result === 'Pass'             ? 'bg-green-100 text-green-700 border-green-300' :
    result === 'Fail'             ? 'bg-red-100 text-red-700 border-red-300' :
    result === 'Conditional Pass' ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
                                    'bg-gray-100 text-gray-600 border-gray-300'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${classes}`}>
      {result}
    </span>
  )
}

/**
 * Color-coded shipment status badge.
 * AC6: the status color makes it immediately clear whether a problematic
 * lot has shipped (red), is blocked (orange), or hasn't shipped (gray).
 */
function ShipmentStatusBadge({ status }: { status: string | null }) {
  if (!status) return (
    <span className="text-xs text-gray-400 italic">Not dispatched</span>
  )
  const classes =
    status === 'Shipped'     ? 'bg-red-100 text-red-700 border-red-300' :    // Shipped with issues → alert
    status === 'On Hold'     ? 'bg-orange-100 text-orange-700 border-orange-300' :
    status === 'Partial'     ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
    status === 'Backordered' ? 'bg-blue-100 text-blue-700 border-blue-300' :
                               'bg-gray-100 text-gray-600 border-gray-300'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${classes}`}>
      {status}
    </span>
  )
}
