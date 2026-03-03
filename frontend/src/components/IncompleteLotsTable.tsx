// src/components/IncompleteLotsTable.tsx
//
// Table showing lots with missing data from one or more functions.
// Supports AC4 (missing data visibility) and AC10 (completeness awareness).
//
// Sorted by overall_completeness ASC — most incomplete lots first, so
// the analyst prioritizes the worst data gaps before a meeting.

import type { IncompleteLotRow } from '../types'
import CompletenessIndicator from './CompletenessIndicator'

interface Props {
  rows:      IncompleteLotRow[];
  isLoading: boolean;
  error?:    string | null;
}

/**
 * Incomplete lots table (AC4, AC10).
 *
 * Shows every lot where overall_completeness < 100%.
 * The `completeness_note` column uses plain English ("Missing inspection data")
 * so the analyst immediately understands the gap without decoding boolean flags.
 *
 * The `last_evaluated_at` column tells the analyst how fresh the score is —
 * if it was evaluated an hour ago and they just added records, they can refresh.
 */
export default function IncompleteLotsTable({ rows, isLoading, error }: Props) {
  if (isLoading) return <div className="text-sm text-gray-500 p-4">Loading…</div>
  if (error)     return <div className="text-red-600 text-sm p-4">{error}</div>
  if (rows.length === 0) return (
    <div className="bg-green-50 border border-green-200 rounded p-4 text-green-700 text-sm">
      ✓ All lots have complete data across all three functions.
    </div>
  )

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-100 flex items-center gap-2">
        <span className="text-sm font-medium text-orange-600">
          ⚠ {rows.length} lot{rows.length !== 1 ? 's' : ''} with incomplete data
        </span>
        <span className="text-xs text-gray-400">(sorted: most incomplete first)</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3 text-left">Lot Code</th>
              <th className="px-4 py-3 text-left">Start Date</th>
              <th className="px-4 py-3 text-center">Data %</th>
              {/* Plain-English completeness note — AC10 */}
              <th className="px-4 py-3 text-left">What's Missing</th>
              <th className="px-4 py-3 text-left">Last Evaluated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr key={row.lot_id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-blue-700">{row.lot_code}</td>
                <td className="px-4 py-3 text-gray-600">
                  {new Date(row.start_date).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <CompletenessIndicator
                    score={row.overall_completeness}
                    hasProduction={row.has_production_data}
                    hasInspection={row.has_inspection_data}
                    hasShipping={row.has_shipping_data}
                  />
                </td>

                {/* Plain-English note — the key AC10 field */}
                <td className="px-4 py-3">
                  <span className="text-orange-700 font-medium text-sm">
                    {row.completeness_note}
                  </span>
                </td>

                {/* Shows how fresh the score is — AC9 trustworthiness */}
                <td className="px-4 py-3 text-gray-400 text-xs">
                  {new Date(row.last_evaluated_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
