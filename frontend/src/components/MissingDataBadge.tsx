// src/components/MissingDataBadge.tsx
//
// Renders "N/A" or "Data Missing" when a field is null/undefined.
// Supports AC4 (missing data must be clearly indicated).
//
// Usage examples:
//   <MissingDataBadge value={row.total_units_produced} format={(v) => v.toLocaleString()} />
//   <MissingDataBadge value={row.ship_date} format={(v) => new Date(v).toLocaleDateString()} />

interface Props<T> {
  /** The value to display (null/undefined = missing). */
  value:  T | null | undefined;
  /** How to format the value if it's present. */
  format?: (v: T) => string;
  /** Custom label for the missing state (default: "N/A"). */
  missingLabel?: string;
}

/**
 * Displays a value if present, or a styled "N/A" badge if missing.
 *
 * The red "N/A" badge makes data gaps immediately visible so analysts
 * don't assume a blank cell means "zero" — it means "no data" (AC4).
 *
 * @template T The type of the value (inferred from the `value` prop).
 */
export default function MissingDataBadge<T>({
  value, format = (v) => String(v), missingLabel = 'N/A',
}: Props<T>) {
  // null or undefined → show missing badge
  if (value === null || value === undefined) {
    return (
      <span
        className="text-xs font-medium text-red-500 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded"
        title="No data available for this field"
      >
        {missingLabel}
      </span>
    )
  }

  // Value is present → render formatted string
  return <span>{format(value)}</span>
}
