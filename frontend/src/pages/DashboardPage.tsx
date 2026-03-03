// src/pages/DashboardPage.tsx
//
// Main dashboard — the analyst's primary view for answering operational
// questions in meetings without opening any spreadsheets (AC7, AC8).
//
// Layout:
//   [Filter Bar]           ← DateRangeFilter (AC2, AC3)
//   [Tabs: Summary | Inspection Issues | Line Issues | Incomplete Lots]
//   [Table for the active tab]
//
// All data is fetched via React Query and cached for 60 seconds (AC9).

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  fetchLotSummary,
  fetchInspectionIssues,
  fetchLineIssues,
  fetchIncompleteLots,
} from '../api/client'
import type { ReportFilters } from '../types'
import DateRangeFilter       from '../components/DateRangeFilter'
import LotSummaryTable       from '../components/LotSummaryTable'
import InspectionIssuesTable from '../components/InspectionIssuesTable'
import LineIssuesTable       from '../components/LineIssuesTable'
import IncompleteLotsTable   from '../components/IncompleteLotsTable'

/** The four tabs available on the dashboard. */
type Tab = 'summary' | 'inspection_issues' | 'line_issues' | 'incomplete'

/**
 * Operations Analytics Dashboard.
 *
 * AC coverage:
 *   AC1, AC2, AC3 — LotSummaryTable with DateRangeFilter
 *   AC4, AC10     — IncompleteLotsTable tab
 *   AC5           — LineIssuesTable tab
 *   AC6           — InspectionIssuesTable tab
 *   AC7, AC8      — entire dashboard design (one page, no spreadsheets)
 *   AC9           — React Query caches responses; same filters → same data
 */
export default function DashboardPage() {
  // Active filter state — shared across all tabs for consistency
  const [filters, setFilters]   = useState<ReportFilters>({})
  const [activeTab, setActiveTab] = useState<Tab>('summary')

  // ── Data fetching via React Query ──────────────────────────────────────────
  // Each query has a unique key that includes the filters.  When filters change,
  // React Query automatically refetches.  Results are cached so switching tabs
  // doesn't re-fetch if the data is still fresh (AC9).

  const summaryQuery = useQuery({
    queryKey: ['lot-summary', filters],
    queryFn:  () => fetchLotSummary(filters),
  })

  const inspectionQuery = useQuery({
    queryKey: ['inspection-issues', filters],
    queryFn:  () => fetchInspectionIssues(filters),
    // Only fetch when this tab is active to avoid unnecessary backend calls
    enabled:  activeTab === 'inspection_issues',
  })

  const lineIssuesQuery = useQuery({
    queryKey: ['line-issues'],
    queryFn:  fetchLineIssues,
    enabled:  activeTab === 'line_issues',
  })

  const incompleteQuery = useQuery({
    queryKey: ['incomplete-lots'],
    queryFn:  fetchIncompleteLots,
    enabled:  activeTab === 'incomplete',
  })

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Operations Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Unified Production, Inspection, and Shipping view — aligned by Lot ID.
          No spreadsheets required.
        </p>
      </div>

      {/* Filter bar — AC2 (lot code), AC3 (date range) */}
      <DateRangeFilter filters={filters} onChange={setFilters} />

      {/* Tab navigation */}
      <div className="flex gap-0 border-b border-gray-200">
        <TabButton
          label="Lot Summary"
          subtitle="AC1, AC2, AC7"
          active={activeTab === 'summary'}
          onClick={() => setActiveTab('summary')}
          badge={summaryQuery.data?.length}
        />
        <TabButton
          label="Inspection Issues"
          subtitle="AC5, AC6"
          active={activeTab === 'inspection_issues'}
          onClick={() => setActiveTab('inspection_issues')}
          badge={inspectionQuery.data?.length}
          alertColor
        />
        <TabButton
          label="Line Issues"
          subtitle="AC5"
          active={activeTab === 'line_issues'}
          onClick={() => setActiveTab('line_issues')}
        />
        <TabButton
          label="Incomplete Lots"
          subtitle="AC4, AC10"
          active={activeTab === 'incomplete'}
          onClick={() => setActiveTab('incomplete')}
          badge={incompleteQuery.data?.length}
          alertColor
        />
      </div>

      {/* Tab content */}
      {activeTab === 'summary' && (
        <LotSummaryTable
          rows={summaryQuery.data ?? []}
          isLoading={summaryQuery.isLoading}
          error={summaryQuery.error?.message}
        />
      )}

      {activeTab === 'inspection_issues' && (
        <>
          {/* Reminder about what this view shows */}
          <div className="text-sm text-gray-500 bg-amber-50 border border-amber-200 rounded p-3">
            <strong>AC6:</strong> Shows lots with flagged inspections and their shipping status.
            Red "Shipped" badge = a problematic lot has already left the facility.
          </div>
          <InspectionIssuesTable
            rows={inspectionQuery.data ?? []}
            isLoading={inspectionQuery.isLoading}
            error={inspectionQuery.error?.message}
          />
        </>
      )}

      {activeTab === 'line_issues' && (
        <>
          <div className="text-sm text-gray-500 bg-blue-50 border border-blue-200 rounded p-3">
            <strong>AC5:</strong> Shows issue counts per production line, sorted by most issues first.
            Helps identify which line needs the most attention.
          </div>
          <LineIssuesTable
            rows={lineIssuesQuery.data ?? []}
            isLoading={lineIssuesQuery.isLoading}
            error={lineIssuesQuery.error?.message}
          />
        </>
      )}

      {activeTab === 'incomplete' && (
        <>
          <div className="text-sm text-gray-500 bg-orange-50 border border-orange-200 rounded p-3">
            <strong>AC4, AC10:</strong> Lists all lots missing data from one or more functions.
            Use this before a meeting to know which gaps exist in the data.
          </div>
          <IncompleteLotsTable
            rows={incompleteQuery.data ?? []}
            isLoading={incompleteQuery.isLoading}
            error={incompleteQuery.error?.message}
          />
        </>
      )}
    </div>
  )
}

// ── Tab button component ───────────────────────────────────────────────────────

interface TabButtonProps {
  label:      string;
  subtitle?:  string;
  active:     boolean;
  onClick:    () => void;
  badge?:     number;
  alertColor?: boolean;
}

/**
 * Individual tab button with optional badge count.
 *
 * @param badge      Number shown in the tab badge (item count).
 * @param alertColor If true, renders the badge in orange (warnings) instead of blue.
 */
function TabButton({ label, subtitle, active, onClick, badge, alertColor }: TabButtonProps) {
  const badgeColor = alertColor && badge && badge > 0
    ? 'bg-orange-500 text-white'
    : 'bg-blue-600 text-white'

  return (
    <button
      onClick={onClick}
      className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors flex flex-col items-start gap-0.5
        ${active
          ? 'border-blue-600 text-blue-700'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }`}
    >
      <div className="flex items-center gap-2">
        {label}
        {/* Badge showing count — omit when undefined (data not yet loaded) */}
        {badge !== undefined && (
          <span className={`text-xs px-1.5 py-0.5 rounded-full ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      {/* AC label sub-text */}
      {subtitle && <span className="text-xs text-gray-400 font-normal">{subtitle}</span>}
    </button>
  )
}
