// src/types/index.ts
//
// TypeScript interfaces that mirror the Pydantic schemas from the backend.
// Keeping these in sync ensures the frontend never misuses an API field.
//
// Naming convention: backend schema names are preserved 1:1 so engineers
// can cross-reference backend docs ↔ frontend types easily.

// ── Lot types ─────────────────────────────────────────────────────────────────

/** Lightweight lot listing item (from GET /api/v1/lots). */
export interface LotSummary {
  lot_id:     number;
  lot_code:   string;
  start_date: string;   // ISO date string "YYYY-MM-DD"
  end_date:   string | null;
}

/** One production run attached to a lot. */
export interface ProductionRecord {
  production_id:    number;
  production_date:  string;
  production_line:  string;
  part_number:      string;
  units_planned:    number;
  quantity_produced: number;
  downtime_min:     number;
  shift:            string;
  line_issue:       boolean;
  primary_issue:    string | null;
  supervisor_notes: string | null;
}

/** One inspection event attached to a lot. */
export interface InspectionRecord {
  inspection_id:    number;
  inspection_date:  string;
  inspection_result: string;   // 'Pass' | 'Fail' | 'Conditional Pass'
  issue_flag:       boolean;
  inspector_notes:  string | null;
}

/** One shipment event attached to a lot. */
export interface ShippingRecord {
  shipping_id:     number;
  ship_date:       string;
  shipment_status: string;    // 'Shipped' | 'Partial' | 'On Hold' | 'Backordered'
  destination:     string;
  customer:        string;
  sales_order:     string | null;
  carrier:         string | null;
  bol_number:      string | null;
  tracking_pro:    string | null;
  qty_shipped:     number;
  hold_reason:     string | null;
  shipping_notes:  string | null;
}

/** Data completeness summary for one lot. */
export interface Completeness {
  has_production_data:  boolean;
  has_inspection_data:  boolean;
  has_shipping_data:    boolean;
  overall_completeness: number;   // 0, 33, 67, or 100
  last_evaluated_at:    string;   // ISO datetime string
}

/** Full lot detail with all child records (from GET /api/v1/lots/{lot_code}). */
export interface LotDetail {
  lot_id:              number;
  lot_code:            string;
  start_date:          string;
  end_date:            string | null;
  production_records:  ProductionRecord[];
  inspection_records:  InspectionRecord[];
  shipping_records:    ShippingRecord[];
  completeness:        Completeness | null;
}

// ── Report types ──────────────────────────────────────────────────────────────

/** One row in the lot summary report (from GET /api/v1/reports/lot-summary). */
export interface LotSummaryRow {
  lot_id:                   number;
  lot_code:                 string;
  start_date:               string;
  end_date:                 string | null;
  // Production
  has_production_data:      boolean;
  production_run_count:     number;
  total_units_produced:     number | null;
  total_units_planned:      number | null;
  attainment_pct:           number | null;
  total_downtime_min:       number | null;
  any_line_issue:           boolean;
  production_issue_count:   number;
  // Inspection
  has_inspection_data:      boolean;
  inspection_count:         number;
  any_inspection_issue:     boolean;
  inspection_issue_count:   number;
  // Shipping
  has_shipping_data:        boolean;
  shipment_count:           number;
  total_qty_shipped:        number | null;
  shipment_statuses:        string[];
  any_shipment_blocked:     boolean;
  // Completeness
  overall_completeness:     number;
  completeness_last_updated: string | null;
}

/** One row in the inspection-issues report (GET /api/v1/reports/inspection-issues). */
export interface InspectionIssueRow {
  lot_id:              number;
  lot_code:            string;
  start_date:          string;
  inspection_date:     string;
  inspection_result:   string;
  inspector_notes:     string | null;
  ship_date:           string | null;
  shipment_status:     string | null;
  hold_reason:         string | null;
  customer:            string | null;
  destination:         string | null;
  overall_completeness: number;
}

/** One row in the incomplete-lots report (GET /api/v1/reports/incomplete-lots). */
export interface IncompleteLotRow {
  lot_id:               number;
  lot_code:             string;
  start_date:           string;
  end_date:             string | null;
  has_production_data:  boolean;
  has_inspection_data:  boolean;
  has_shipping_data:    boolean;
  overall_completeness: number;
  last_evaluated_at:    string;
  completeness_note:    string;   // Plain-English description
}

/** One row in the line-issues report (GET /api/v1/reports/line-issues). */
export interface LineIssueRow {
  production_line:          string;
  total_runs:               number;
  issue_runs:               number;
  issue_rate_pct:           number;
  tool_wear_count:          number;
  sensor_fault_count:       number;
  material_shortage_count:  number;
  changeover_delay_count:   number;
  quality_hold_count:       number;
  operator_training_count:  number;
}

// ── Filter types ──────────────────────────────────────────────────────────────

/** Shape of query parameters sent to filtered report endpoints. */
export interface ReportFilters {
  lot_code?:  string;
  date_from?: string;   // "YYYY-MM-DD"
  date_to?:   string;   // "YYYY-MM-DD"
}
