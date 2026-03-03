// src/components/LineIssuesTable.tsx
//
// Table showing production issues grouped and ranked by production line (AC5).
// Answers: "Which line had the most problems, and what kind?"

import type { LineIssueRow } from '../types'

interface Props {
  rows:      LineIssueRow[];
  isLoading: boolean;
  error?:    string | null;
}

/**
 * Production line issue summary table (AC5).
 *
 * Sorted by issue_runs DESC (most problematic line first) so the analyst
 * can immediately answer "Which line needs attention?" in a meeting.
 *
 * The issue rate bar provides a visual comparison between lines.
 */
export default function LineIssuesTable({ rows, isLoading, error }: Props) {
  if (isLoading) return <div className="text-sm text-gray-500 p-4">Loading…</div>
  if (error)     return <div className="text-red-600 text-sm p-4">{error}</div>
  if (rows.length === 0) return (
    <div className="text-gray-400 text-sm p-4">No production data available.</div>
  )

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3 text-left">Line</th>
              <th className="px-4 py-3 text-right">Total Runs</th>
              <th className="px-4 py-3 text-right">Issue Runs</th>
              <th className="px-4 py-3 text-left">Issue Rate</th>
              <th className="px-4 py-3 text-right" title="Tool wear">Tool Wear</th>
              <th className="px-4 py-3 text-right" title="Sensor fault">Sensor</th>
              <th className="px-4 py-3 text-right" title="Material shortage">Material</th>
              <th className="px-4 py-3 text-right" title="Changeover delay">Changeover</th>
              <th className="px-4 py-3 text-right" title="Quality hold">Quality</th>
              <th className="px-4 py-3 text-right" title="Operator training">Training</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr key={row.production_line} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-800">{row.production_line}</td>
                <td className="px-4 py-3 text-right text-gray-600">{row.total_runs}</td>
                <td className="px-4 py-3 text-right">
                  {/* Red count if any issues, otherwise green zero */}
                  <span className={row.issue_runs > 0 ? 'font-bold text-red-600' : 'text-green-600'}>
                    {row.issue_runs}
                  </span>
                </td>

                {/* Visual issue rate bar — makes comparison between lines instant */}
                <td className="px-4 py-3 min-w-[140px]">
                  <IssueRateBar rate={row.issue_rate_pct} />
                </td>

                {/* Issue type breakdown counts */}
                <td className="px-4 py-3 text-right">{row.tool_wear_count || '—'}</td>
                <td className="px-4 py-3 text-right">{row.sensor_fault_count || '—'}</td>
                <td className="px-4 py-3 text-right">{row.material_shortage_count || '—'}</td>
                <td className="px-4 py-3 text-right">{row.changeover_delay_count || '—'}</td>
                <td className="px-4 py-3 text-right">{row.quality_hold_count || '—'}</td>
                <td className="px-4 py-3 text-right">{row.operator_training_count || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/**
 * Horizontal bar + percentage label visualizing the issue rate.
 *
 * @param rate Percentage 0–100.
 *
 * Color scale:
 *   0%      → green (no issues)
 *   1–25%   → yellow (minor)
 *   26–50%  → orange (moderate)
 *   >50%    → red (high)
 */
function IssueRateBar({ rate }: { rate: number }) {
  const barColor =
    rate === 0   ? 'bg-green-400' :
    rate <= 25   ? 'bg-yellow-400' :
    rate <= 50   ? 'bg-orange-400' :
                   'bg-red-500'

  return (
    <div className="flex items-center gap-2">
      {/* Background track */}
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        {/* Fill — width is the rate percentage; min 2px so 0% still renders */}
        <div
          className={`h-2 rounded-full transition-all ${barColor}`}
          style={{ width: `${Math.max(rate, rate > 0 ? 4 : 0)}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-10 text-right">{rate}%</span>
    </div>
  )
}
