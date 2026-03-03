// src/components/CompletenessIndicator.tsx
//
// Visual indicator for a lot's data completeness percentage.
// Supports AC4 (missing data visibility) and AC10 (data completeness awareness).
//
// Shows:
//   - A colored badge with the percentage (0%, 33%, 67%, 100%)
//   - Color coding: red=0%, orange=33%, yellow=67%, green=100%
//   - Three boolean dots showing which functions have data

interface Props {
  /** Integer percentage: 0, 33, 67, or 100. */
  score: number;
  hasProduction: boolean;
  hasInspection: boolean;
  hasShipping:   boolean;
  /** If true, show only the badge without the function dots. */
  compact?: boolean;
}

/**
 * Completeness badge + function coverage dots.
 *
 * Color scale:
 *   0%  → red-600   ("No data in any function")
 *   33% → orange-500
 *   67% → yellow-500 ("Missing one function")
 *   100% → green-600 ("All data present")
 *
 * The dots below the badge show WHICH functions are present (P / I / S),
 * so the analyst can tell at a glance what's missing without reading text.
 */
export default function CompletenessIndicator({
  score, hasProduction, hasInspection, hasShipping, compact = false,
}: Props) {
  // Determine badge color based on the score value
  // Using Tailwind's JIT classes — these must be complete strings (not dynamic)
  // so Tailwind's purge scanner can find them.
  const badgeColor =
    score === 100 ? 'bg-green-100 text-green-700 border-green-300' :
    score >= 67   ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
    score >= 33   ? 'bg-orange-100 text-orange-700 border-orange-300' :
                   'bg-red-100 text-red-700 border-red-300';

  return (
    <div className="flex flex-col items-center gap-1">
      {/* Percentage badge */}
      <span className={`text-xs font-bold px-2 py-0.5 rounded border ${badgeColor}`}>
        {score}%
      </span>

      {/* Function coverage dots — only shown when compact=false */}
      {!compact && (
        <div className="flex gap-1 text-xs">
          {/* Each dot: filled = data present, hollow = missing */}
          <Dot label="P" active={hasProduction} title="Production data" />
          <Dot label="I" active={hasInspection} title="Inspection data" />
          <Dot label="S" active={hasShipping}   title="Shipping data"   />
        </div>
      )}
    </div>
  )
}

/** Single function coverage dot. */
function Dot({ label, active, title }: { label: string; active: boolean; title: string }) {
  return (
    <span
      title={title}  // Browser tooltip on hover
      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border
        ${active
          ? 'bg-blue-600 text-white border-blue-700'   // Filled = data present
          : 'bg-white text-gray-400 border-gray-300'   // Hollow = missing (AC4)
        }`}
    >
      {label}
    </span>
  )
}
