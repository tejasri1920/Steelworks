// src/pages/LotDetailPage.tsx
//
// Full drill-down view for a single lot.
// Reached by clicking a lot code in the Dashboard table.
//
// Displays all three functions' records plus the completeness indicator.
// This is the "replaced three spreadsheets" experience (AC1, AC8).
//
// URL: /lots/:lot_code

import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchLotDetail } from '../api/client'
import type { ProductionRecord, InspectionRecord, ShippingRecord } from '../types'
import CompletenessIndicator from '../components/CompletenessIndicator'
import MissingDataBadge from '../components/MissingDataBadge'

/**
 * Lot detail page — full cross-functional view for one lot (AC1, AC2, AC8).
 *
 * Sections:
 *   1. Header: lot code, dates, completeness indicator
 *   2. Production records table
 *   3. Inspection records table
 *   4. Shipping records table
 *
 * Each section's presence (or absence) directly shows the analyst which
 * functions have data for this lot (AC4).
 */
export default function LotDetailPage() {
  // Extract the :lot_code parameter from the URL (e.g., /lots/LOT-20260112-001)
  const { lot_code } = useParams<{ lot_code: string }>()

  const { data: lot, isLoading, error } = useQuery({
    queryKey: ['lot-detail', lot_code],
    queryFn:  () => fetchLotDetail(lot_code!),
    enabled:  !!lot_code,   // Don't fetch if lot_code is somehow undefined
    retry: 1,
  })

  // ── Loading state ──────────────────────────────────────────────────────────
  if (isLoading) return (
    <div className="space-y-4">
      <div className="h-8 w-64 bg-gray-200 animate-pulse rounded" />
      <div className="h-48 bg-gray-100 animate-pulse rounded-lg" />
    </div>
  )

  // ── Error state (includes 404) ─────────────────────────────────────────────
  if (error) return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700">
      <h2 className="font-bold text-lg mb-2">Lot not found</h2>
      <p className="text-sm">
        Lot code <code className="bg-red-100 px-1 rounded">{lot_code}</code> could not be found.
        It may not exist or may have been removed from the system.
      </p>
      <Link to="/" className="mt-4 inline-block text-sm text-blue-700 hover:underline">
        ← Back to Dashboard
      </Link>
    </div>
  )

  if (!lot) return null

  const comp = lot.completeness

  return (
    <div className="space-y-6">

      {/* ── Back navigation ──────────────────────────────────────────────── */}
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← Back to Dashboard
      </Link>

      {/* ── Lot header ───────────────────────────────────────────────────── */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-800 font-mono">{lot.lot_code}</h1>
            <div className="text-sm text-gray-500 mt-1 space-x-4">
              <span>Start: <strong>{new Date(lot.start_date).toLocaleDateString()}</strong></span>
              {lot.end_date && (
                <span>End: <strong>{new Date(lot.end_date).toLocaleDateString()}</strong></span>
              )}
              {!lot.end_date && (
                <span className="text-blue-600 font-medium">● Open lot</span>
              )}
            </div>
          </div>

          {/* Completeness indicator — AC4, AC10 */}
          {comp && (
            <div className="flex flex-col items-center gap-1">
              <span className="text-xs text-gray-400 font-medium">Data Coverage</span>
              <CompletenessIndicator
                score={comp.overall_completeness}
                hasProduction={comp.has_production_data}
                hasInspection={comp.has_inspection_data}
                hasShipping={comp.has_shipping_data}
              />
              <span className="text-xs text-gray-400">
                Updated {new Date(comp.last_evaluated_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {/* Completeness warning banner — AC4, AC10 */}
        {comp && comp.overall_completeness < 100 && (
          <div className="mt-4 bg-orange-50 border border-orange-200 rounded p-3 text-sm text-orange-700">
            ⚠ <strong>Incomplete data:</strong>{' '}
            {!comp.has_production_data && 'Production records are missing. '}
            {!comp.has_inspection_data && 'Inspection records are missing. '}
            {!comp.has_shipping_data   && 'Shipping records are missing. '}
            Results shown below may not reflect the full picture.
          </div>
        )}
      </div>

      {/* ── Production records ───────────────────────────────────────────── */}
      <Section
        title="Production Records"
        count={lot.production_records.length}
        hasData={comp?.has_production_data ?? lot.production_records.length > 0}
        acLabel="AC1"
      >
        {lot.production_records.length > 0
          ? <ProductionTable records={lot.production_records} />
          : <EmptyFunctionCard function_name="production" />
        }
      </Section>

      {/* ── Inspection records ───────────────────────────────────────────── */}
      <Section
        title="Inspection Records"
        count={lot.inspection_records.length}
        hasData={comp?.has_inspection_data ?? lot.inspection_records.length > 0}
        acLabel="AC1, AC5"
      >
        {lot.inspection_records.length > 0
          ? <InspectionTable records={lot.inspection_records} />
          : <EmptyFunctionCard function_name="inspection" />
        }
      </Section>

      {/* ── Shipping records ─────────────────────────────────────────────── */}
      <Section
        title="Shipping Records"
        count={lot.shipping_records.length}
        hasData={comp?.has_shipping_data ?? lot.shipping_records.length > 0}
        acLabel="AC1, AC6"
      >
        {lot.shipping_records.length > 0
          ? <ShippingTable records={lot.shipping_records} />
          : <EmptyFunctionCard function_name="shipping" />
        }
      </Section>
    </div>
  )
}

// ── Section wrapper ────────────────────────────────────────────────────────────

interface SectionProps {
  title:    string;
  count:    number;
  hasData:  boolean;
  acLabel:  string;
  children: React.ReactNode;
}

/**
 * Section wrapper with a header showing title, record count, and AC label.
 * When hasData = false, a warning badge shows this function has no records.
 */
function Section({ title, count, hasData, acLabel, children }: SectionProps) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <h2 className="text-base font-semibold text-gray-700">{title}</h2>
        {hasData
          ? <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{count} record{count !== 1 ? 's' : ''}</span>
          : <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded border border-red-200">No data</span>
        }
        <span className="text-xs text-gray-400 ml-auto">{acLabel}</span>
      </div>
      {children}
    </div>
  )
}

/** Shown when a function has no records for this lot (AC4). */
function EmptyFunctionCard({ function_name }: { function_name: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
      <strong>Data Missing:</strong> No {function_name} records exist for this lot.
      This gap is tracked in the <em>Incomplete Lots</em> report.
    </div>
  )
}

// ── Production table ───────────────────────────────────────────────────────────

function ProductionTable({ records }: { records: ProductionRecord[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
          <tr>
            <th className="px-4 py-3 text-left">Date</th>
            <th className="px-4 py-3 text-left">Line</th>
            <th className="px-4 py-3 text-left">Shift</th>
            <th className="px-4 py-3 text-left">Part #</th>
            <th className="px-4 py-3 text-right">Planned</th>
            <th className="px-4 py-3 text-right">Produced</th>
            <th className="px-4 py-3 text-right">Downtime (min)</th>
            <th className="px-4 py-3 text-center">Line Issue</th>
            <th className="px-4 py-3 text-left">Primary Issue</th>
            <th className="px-4 py-3 text-left">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {records.map((pr) => (
            <tr key={pr.production_id} className={pr.line_issue ? 'bg-red-50' : ''}>
              <td className="px-4 py-3">{new Date(pr.production_date).toLocaleDateString()}</td>
              <td className="px-4 py-3">{pr.production_line}</td>
              <td className="px-4 py-3">{pr.shift}</td>
              <td className="px-4 py-3 font-mono text-xs">{pr.part_number}</td>
              <td className="px-4 py-3 text-right">{pr.units_planned.toLocaleString()}</td>
              <td className="px-4 py-3 text-right">{pr.quantity_produced.toLocaleString()}</td>
              <td className="px-4 py-3 text-right">{pr.downtime_min}</td>
              <td className="px-4 py-3 text-center">
                {pr.line_issue
                  ? <span className="text-xs font-bold text-red-600 bg-red-100 px-1.5 py-0.5 rounded">YES</span>
                  : <span className="text-xs text-green-600">—</span>
                }
              </td>
              <td className="px-4 py-3 text-xs">
                <MissingDataBadge value={pr.primary_issue} missingLabel="—" />
              </td>
              <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">
                <MissingDataBadge value={pr.supervisor_notes} missingLabel="—" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Inspection table ───────────────────────────────────────────────────────────

function InspectionTable({ records }: { records: InspectionRecord[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
          <tr>
            <th className="px-4 py-3 text-left">Date</th>
            <th className="px-4 py-3 text-center">Result</th>
            <th className="px-4 py-3 text-center">Issue Flag</th>
            <th className="px-4 py-3 text-left">Inspector Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {records.map((ir) => (
            <tr key={ir.inspection_id} className={ir.issue_flag ? 'bg-red-50' : ''}>
              <td className="px-4 py-3">{new Date(ir.inspection_date).toLocaleDateString()}</td>
              <td className="px-4 py-3 text-center">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded border
                  ${ir.inspection_result === 'Pass'             ? 'bg-green-100 text-green-700 border-green-300' :
                    ir.inspection_result === 'Fail'             ? 'bg-red-100 text-red-700 border-red-300' :
                                                                  'bg-yellow-100 text-yellow-700 border-yellow-300'}`}>
                  {ir.inspection_result}
                </span>
              </td>
              <td className="px-4 py-3 text-center">
                {ir.issue_flag
                  ? <span className="text-xs font-bold text-red-600">⚠ FLAGGED</span>
                  : <span className="text-xs text-green-600">✓ Clear</span>
                }
              </td>
              <td className="px-4 py-3 text-xs text-gray-500">
                <MissingDataBadge value={ir.inspector_notes} missingLabel="—" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Shipping table ─────────────────────────────────────────────────────────────

function ShippingTable({ records }: { records: ShippingRecord[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs text-gray-500 uppercase tracking-wider">
          <tr>
            <th className="px-4 py-3 text-left">Ship Date</th>
            <th className="px-4 py-3 text-center">Status</th>
            <th className="px-4 py-3 text-left">Customer</th>
            <th className="px-4 py-3 text-left">Destination</th>
            <th className="px-4 py-3 text-right">Qty Shipped</th>
            <th className="px-4 py-3 text-left">Sales Order</th>
            <th className="px-4 py-3 text-left">Carrier</th>
            <th className="px-4 py-3 text-left">BOL #</th>
            <th className="px-4 py-3 text-left">Hold Reason</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {records.map((sr) => (
            <tr
              key={sr.shipping_id}
              className={
                sr.shipment_status === 'On Hold'
                  ? 'bg-orange-50'
                  : sr.shipment_status === 'Backordered'
                  ? 'bg-blue-50'
                  : ''
              }
            >
              <td className="px-4 py-3">{new Date(sr.ship_date).toLocaleDateString()}</td>
              <td className="px-4 py-3 text-center">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded border
                  ${sr.shipment_status === 'Shipped'     ? 'bg-green-100 text-green-700 border-green-300' :
                    sr.shipment_status === 'On Hold'     ? 'bg-orange-100 text-orange-700 border-orange-300' :
                    sr.shipment_status === 'Partial'     ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
                                                          'bg-blue-100 text-blue-700 border-blue-300'}`}>
                  {sr.shipment_status}
                </span>
              </td>
              <td className="px-4 py-3">{sr.customer}</td>
              <td className="px-4 py-3">{sr.destination}</td>
              <td className="px-4 py-3 text-right">{sr.qty_shipped.toLocaleString()}</td>
              <td className="px-4 py-3 text-xs font-mono">
                <MissingDataBadge value={sr.sales_order} missingLabel="—" />
              </td>
              <td className="px-4 py-3 text-xs">
                <MissingDataBadge value={sr.carrier} missingLabel="Customer pickup" />
              </td>
              <td className="px-4 py-3 text-xs font-mono">
                <MissingDataBadge value={sr.bol_number} missingLabel="—" />
              </td>
              <td className="px-4 py-3 text-xs text-orange-700 font-medium">
                <MissingDataBadge value={sr.hold_reason} missingLabel="—" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
