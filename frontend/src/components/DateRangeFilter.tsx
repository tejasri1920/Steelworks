// src/components/DateRangeFilter.tsx
//
// A controlled date-range picker with an optional lot-code search field.
// Supports AC3 (date-based filtering) and AC2 (lot-based alignment).
//
// "Controlled" means the parent component owns the filter state and passes
// it down via props.  When the user changes a field, onChange fires with
// the new filter values, and the parent re-fetches the data.

import { useState } from 'react'
import type { ReportFilters } from '../types'

interface Props {
  /** Current filter values (controlled from parent). */
  filters:  ReportFilters;
  /** Called whenever any filter value changes. */
  onChange: (filters: ReportFilters) => void;
  /** Whether to show the lot code search input (default: true). */
  showLotCode?: boolean;
}

/**
 * Filter panel for lot code and date range.
 *
 * Layout:
 *   [Lot Code: __________] [From: ________] [To: ________] [Clear]
 *
 * Pressing Enter in the lot code field or clicking a date triggers onChange
 * so the parent component updates its query immediately.
 *
 * AC2: lot_code filter aligns records to a specific lot.
 * AC3: date_from / date_to filter by date range.
 */
export default function DateRangeFilter({ filters, onChange, showLotCode = true }: Props) {
  // Local draft state — lets the user type without triggering a search
  // on every keystroke.  Applied when they press Enter or click Apply.
  const [draft, setDraft] = useState<ReportFilters>(filters)

  /** Apply the current draft filters → triggers parent's onChange. */
  function handleApply() {
    // Trim whitespace from the lot code to avoid accidental no-match
    onChange({ ...draft, lot_code: draft.lot_code?.trim() || undefined })
  }

  /** Reset all filters to empty. */
  function handleClear() {
    const empty: ReportFilters = {}
    setDraft(empty)
    onChange(empty)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex flex-wrap gap-3 items-end">
        {/* Lot Code search — AC2 */}
        {showLotCode && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Lot Code
            </label>
            <input
              type="text"
              placeholder="e.g. LOT-20260112-001"
              value={draft.lot_code ?? ''}
              onChange={(e) => setDraft({ ...draft, lot_code: e.target.value })}
              // Apply on Enter key for keyboard users
              onKeyDown={(e) => e.key === 'Enter' && handleApply()}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm w-52
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Date From — AC3 */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Start Date (From)
          </label>
          <input
            type="date"
            value={draft.date_from ?? ''}
            onChange={(e) => setDraft({ ...draft, date_from: e.target.value || undefined })}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Date To — AC3 */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            End Date (To)
          </label>
          <input
            type="date"
            value={draft.date_to ?? ''}
            onChange={(e) => setDraft({ ...draft, date_to: e.target.value || undefined })}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleApply}
            className="bg-blue-700 text-white px-4 py-1.5 rounded text-sm font-medium
                       hover:bg-blue-800 transition-colors"
          >
            Apply
          </button>
          <button
            onClick={handleClear}
            className="bg-gray-100 text-gray-600 px-4 py-1.5 rounded text-sm font-medium
                       hover:bg-gray-200 transition-colors border border-gray-300"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Active filter indicator — shows the analyst what is currently filtered */}
      {(filters.lot_code || filters.date_from || filters.date_to) && (
        <div className="mt-2 text-xs text-blue-600 flex gap-2 flex-wrap">
          <span className="font-semibold">Active filters:</span>
          {filters.lot_code  && <span className="bg-blue-50 px-2 py-0.5 rounded">Lot: {filters.lot_code}</span>}
          {filters.date_from && <span className="bg-blue-50 px-2 py-0.5 rounded">From: {filters.date_from}</span>}
          {filters.date_to   && <span className="bg-blue-50 px-2 py-0.5 rounded">To: {filters.date_to}</span>}
        </div>
      )}
    </div>
  )
}
