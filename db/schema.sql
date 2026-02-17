-- ============================================================
-- Ops Analytics Schema — Corrected Physical DDL
-- Fixes: completeness scoring, DELETE trigger handling,
--        ON DELETE RESTRICT, removed unused uuid-ossp extension
-- Best practices: CHECK on controlled vocabularies,
--        SMALLINT percentage for completeness score,
--        removed redundant updated_at from data_completeness
-- ============================================================

-- ============================================================
-- CORE TABLE: lots
-- ============================================================
CREATE TABLE lots (
    lot_id      SERIAL PRIMARY KEY,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_lots_dates CHECK (end_date >= start_date)
);

-- Auto-update updated_at on lots row changes
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_lots_updated_at
    BEFORE UPDATE ON lots
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- CHILD TABLE: production_records
-- FIX: ON DELETE RESTRICT (was CASCADE) to prevent silent
--      history loss when a lot is accidentally deleted
-- ============================================================
CREATE TABLE production_records (
    production_id   SERIAL PRIMARY KEY,
    lot_id          INTEGER NOT NULL
                        REFERENCES lots(lot_id) ON DELETE RESTRICT,
    production_date DATE NOT NULL,
    production_line VARCHAR(50) NOT NULL
                        CHECK (production_line IN ('Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5')),
    quantity_produced INTEGER NOT NULL CHECK (quantity_produced >= 0),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- CHILD TABLE: inspection_records
-- FIX: ON DELETE RESTRICT (was CASCADE)
-- ============================================================
CREATE TABLE inspection_records (
    inspection_id   SERIAL PRIMARY KEY,
    lot_id          INTEGER NOT NULL
                        REFERENCES lots(lot_id) ON DELETE RESTRICT,
    inspection_date DATE NOT NULL,
    inspection_result VARCHAR(20)
                        CHECK (inspection_result IN ('Pass', 'Fail', 'Hold')),
    issue_flag      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- CHILD TABLE: shipping_records
-- FIX: ON DELETE RESTRICT (was CASCADE)
-- ============================================================
CREATE TABLE shipping_records (
    shipping_id     SERIAL PRIMARY KEY,
    lot_id          INTEGER NOT NULL
                        REFERENCES lots(lot_id) ON DELETE RESTRICT,
    ship_date       DATE NOT NULL,
    shipment_status VARCHAR(20) NOT NULL
                        CHECK (shipment_status IN ('Shipped', 'Partial', 'On Hold', 'Pending')),
    destination     VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- SUMMARY TABLE: data_completeness
-- One-to-one with lots. Maintained by trigger below.
-- FIX: ON DELETE RESTRICT (was CASCADE)
-- BEST PRACTICE: overall_completeness stored as SMALLINT (0–100)
--   instead of DECIMAL — integer over float per convention.
--   updated_at removed — trigger-managed table; child table
--   timestamps already capture when changes occurred.
-- ============================================================
CREATE TABLE data_completeness (
    lot_id               INTEGER PRIMARY KEY
                             REFERENCES lots(lot_id) ON DELETE RESTRICT,
    has_production_data  BOOLEAN NOT NULL DEFAULT FALSE,
    has_inspection_data  BOOLEAN NOT NULL DEFAULT FALSE,
    has_shipping_data    BOOLEAN NOT NULL DEFAULT FALSE,
    overall_completeness SMALLINT NOT NULL DEFAULT 0
                             CHECK (overall_completeness BETWEEN 0 AND 100)
);


-- ============================================================
-- INDEXES
-- Composite indexes aligned to AC1–AC3, AC5–AC7 query patterns
-- ============================================================
CREATE INDEX idx_production_lot_date   ON production_records  (lot_id, production_date);
CREATE INDEX idx_production_line       ON production_records  (production_line);
CREATE INDEX idx_inspection_lot_date   ON inspection_records  (lot_id, inspection_date, issue_flag);
CREATE INDEX idx_shipping_lot_date     ON shipping_records    (lot_id, ship_date, shipment_status);
CREATE INDEX idx_lots_dates            ON lots                (start_date, end_date);


-- ============================================================
-- TRIGGER FUNCTION: update_completeness
--
-- FIX 1: completeness is now binary-presence based, not count-based.
--         A lot with 10 production rows and 0 inspection/shipping rows
--         correctly scores 0.3333, not 10/3 = 3.333.
--
-- FIX 2: DELETE operations set NEW to NULL in PostgreSQL.
--         We resolve the correct lot_id using TG_OP to choose
--         between OLD and NEW before any lookups.
-- ============================================================
CREATE OR REPLACE FUNCTION update_completeness()
RETURNS TRIGGER AS $$
DECLARE
    v_lot_id     INTEGER;
    v_has_prod   BOOLEAN;
    v_has_insp   BOOLEAN;
    v_has_ship   BOOLEAN;
    v_score      SMALLINT;
BEGIN
    v_lot_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.lot_id ELSE NEW.lot_id END;

    -- NULL safety: guard against concurrent deletes removing the parent lot
    -- between trigger fire and lookup execution
    IF v_lot_id IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;

    -- EXISTS halts at first match; avoids full COUNT(*) scan per function
    v_has_prod := EXISTS (SELECT 1 FROM production_records WHERE lot_id = v_lot_id);
    v_has_insp := EXISTS (SELECT 1 FROM inspection_records WHERE lot_id = v_lot_id);
    v_has_ship := EXISTS (SELECT 1 FROM shipping_records   WHERE lot_id = v_lot_id);

    -- Score stored as integer percentage (0, 33, 67, 100)
    v_score := (
        (CASE WHEN v_has_prod THEN 1 ELSE 0 END) +
        (CASE WHEN v_has_insp THEN 1 ELSE 0 END) +
        (CASE WHEN v_has_ship THEN 1 ELSE 0 END)
    ) * 100 / 3;

    INSERT INTO data_completeness (lot_id, has_production_data, has_inspection_data, has_shipping_data, overall_completeness)
    VALUES (v_lot_id, v_has_prod, v_has_insp, v_has_ship, v_score)
    ON CONFLICT (lot_id) DO UPDATE SET
        has_production_data  = v_has_prod,
        has_inspection_data  = v_has_insp,
        has_shipping_data    = v_has_ship,
        overall_completeness = v_score;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TRIGGERS: apply completeness refresh to all child tables
-- ============================================================
CREATE TRIGGER trig_update_completeness_prod
    AFTER INSERT OR UPDATE OR DELETE ON production_records
    FOR EACH ROW EXECUTE FUNCTION update_completeness();

CREATE TRIGGER trig_update_completeness_insp
    AFTER INSERT OR UPDATE OR DELETE ON inspection_records
    FOR EACH ROW EXECUTE FUNCTION update_completeness();

CREATE TRIGGER trig_update_completeness_ship
    AFTER INSERT OR UPDATE OR DELETE ON shipping_records
    FOR EACH ROW EXECUTE FUNCTION update_completeness();
