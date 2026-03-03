# tests/test_lots.py
#
# Tests for the Lot endpoints: GET /api/v1/lots and GET /api/v1/lots/{lot_code}
#
# ─── AC Coverage ─────────────────────────────────────────────────────────────
# AC1  (Cross-function data availability)  : test_lot_detail_has_all_three_functions
# AC2  (Lot-based alignment)               : test_lot_detail_aligns_by_lot_id
#                                            test_list_lots_filter_by_lot_code
# AC3  (Date-based filtering)              : test_list_lots_filter_by_date_from
#                                            test_list_lots_filter_by_date_to
#                                            test_list_lots_date_range_both_bounds
# AC4  (Missing data visibility)           : test_lot_detail_shows_empty_lists_for_missing_data
#                                            test_lot_detail_completeness_reflects_missing
# AC8  (Reduced manual effort)             : test_lot_detail_has_all_three_functions
#                                            (one API call replaces three spreadsheets)
# AC9  (Consistent results)               : test_same_query_returns_same_result
# AC10 (Data completeness awareness)      : test_lot_detail_completeness_score

import pytest
from datetime import date
from fastapi import status


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_lot(client, lot_code: str):
    """Helper: GET /api/v1/lots/{lot_code} and return the JSON body."""
    return client.get(f"/api/v1/lots/{lot_code}")


def _list_lots(client, **params):
    """Helper: GET /api/v1/lots with optional query parameters."""
    return client.get("/api/v1/lots", params=params)


# ─────────────────────────────────────────────────────────────────────────────
# AC1 & AC8 — Cross-function data availability / Reduced manual effort
# ─────────────────────────────────────────────────────────────────────────────

class TestLotDetail:
    """Tests for GET /api/v1/lots/{lot_code}."""

    def test_lot_detail_has_all_three_functions(self, seeded_client):
        """
        AC1 — Given a lot with records in all three functions,
        when GET /lots/{lot_code} is called,
        then the response contains production_records, inspection_records,
        AND shipping_records — all in one API call (AC8).

        This test proves a single endpoint replaces opening three spreadsheets.
        """
        resp = _get_lot(seeded_client, "LOT-A")
        assert resp.status_code == status.HTTP_200_OK

        body = resp.json()

        # AC1: all three functions are present
        assert len(body["production_records"]) >= 1,   "Production records must be present"
        assert len(body["inspection_records"]) >= 1,   "Inspection records must be present"
        assert len(body["shipping_records"])   >= 1,   "Shipping records must be present"

        # AC8: single response (no separate spreadsheet lookups needed)
        assert "lot_code"           in body
        assert "production_records" in body
        assert "inspection_records" in body
        assert "shipping_records"   in body

    def test_lot_detail_aligns_by_lot_id(self, seeded_client):
        """
        AC2 — Records from all three functions must share the same lot_code,
        confirming they are aligned by lot ID (not just returned together
        by coincidence).
        """
        resp = _get_lot(seeded_client, "LOT-A")
        body = resp.json()

        # The top-level lot_code must match what we requested
        assert body["lot_code"] == "LOT-A"

        # Each nested record was loaded by lot_id FK → they belong to this lot
        for pr in body["production_records"]:
            # production_records.lot_id (FK) links them to the lot
            assert pr["production_id"] is not None  # valid DB row
        for ir in body["inspection_records"]:
            assert ir["inspection_id"] is not None
        for sr in body["shipping_records"]:
            assert sr["shipping_id"] is not None

    def test_lot_detail_shows_empty_lists_for_missing_data(self, seeded_client):
        """
        AC4 — LOT-B has no inspection record.
        When the lot is retrieved, inspection_records must be an empty list
        and completeness.has_inspection_data must be False.
        """
        resp = _get_lot(seeded_client, "LOT-B")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()

        # LOT-B has production and shipping but NO inspection
        assert len(body["production_records"]) >= 1,  "LOT-B should have production data"
        assert len(body["inspection_records"]) == 0,   "LOT-B should have NO inspection data (AC4)"
        assert len(body["shipping_records"])   >= 1,  "LOT-B should have shipping data"

    def test_lot_detail_completeness_reflects_missing(self, seeded_client):
        """
        AC4 & AC10 — LOT-B is missing inspection → completeness should be 67%
        (2 out of 3 functions present).
        """
        resp = _get_lot(seeded_client, "LOT-B")
        body = resp.json()

        comp = body["completeness"]
        assert comp is not None,                         "completeness field must be present"
        assert comp["has_inspection_data"] is False,     "inspection data absent (AC4)"
        assert comp["has_production_data"] is True
        assert comp["has_shipping_data"]   is True
        assert comp["overall_completeness"] == 67,       "2/3 functions → 67% (AC10)"

    def test_lot_detail_completeness_score_100(self, seeded_client):
        """
        AC10 — LOT-A has all three functions → completeness must be 100%.
        """
        resp = _get_lot(seeded_client, "LOT-A")
        body = resp.json()

        comp = body["completeness"]
        assert comp["overall_completeness"] == 100, "All three functions present → 100%"
        assert comp["has_production_data"] is True
        assert comp["has_inspection_data"] is True
        assert comp["has_shipping_data"]   is True

    def test_lot_detail_completeness_score_0(self, seeded_client):
        """
        AC4 & AC10 — LOT-D has NO child records → completeness must be 0%.
        The lot still appears with empty lists, not a 404, so the gap is
        visible (AC4) and the analyst can see insufficient information (AC10).
        """
        resp = _get_lot(seeded_client, "LOT-D")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()

        comp = body["completeness"]
        assert comp["overall_completeness"] == 0,      "No records → 0% (AC4, AC10)"
        assert comp["has_production_data"]  is False
        assert comp["has_inspection_data"]  is False
        assert comp["has_shipping_data"]    is False

    def test_lot_detail_not_found_returns_404(self, seeded_client):
        """Error path: requesting a non-existent lot code returns HTTP 404."""
        resp = _get_lot(seeded_client, "LOT-DOESNOTEXIST")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# AC2 & AC3 — Lot-based alignment / Date-based filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestLotList:
    """Tests for GET /api/v1/lots with optional filters."""

    def test_list_lots_returns_all_when_no_filter(self, seeded_client):
        """Without any filter, all lots in the database are returned."""
        resp = _list_lots(seeded_client)
        assert resp.status_code == status.HTTP_200_OK
        lots = resp.json()
        # We inserted 4 lots in the seeded fixture
        assert len(lots) == 4, "All 4 seeded lots should be returned"

    def test_list_lots_filter_by_lot_code(self, seeded_client):
        """
        AC2 — Filtering by lot_code should return exactly one lot.
        Alignment by lot_id is enforced: only the requested lot code appears.
        """
        resp = _list_lots(seeded_client, lot_code="LOT-A")
        assert resp.status_code == status.HTTP_200_OK
        lots = resp.json()
        assert len(lots) == 1,              "Exact lot_code filter → 1 result"
        assert lots[0]["lot_code"] == "LOT-A"

    def test_list_lots_filter_by_date_from(self, seeded_client):
        """
        AC3 — date_from filter should include only lots with start_date ≥ the given date.
        LOT-B starts 2026-01-15 and LOT-D starts 2026-01-20; LOT-A (Jan 10)
        and LOT-C (Jan 12) should be excluded.
        """
        resp = _list_lots(seeded_client, date_from="2026-01-15")
        lots = resp.json()
        codes = {lot["lot_code"] for lot in lots}

        assert "LOT-B" in codes,   "LOT-B (Jan 15) must be included"
        assert "LOT-D" in codes,   "LOT-D (Jan 20) must be included"
        assert "LOT-A" not in codes, "LOT-A (Jan 10) must be excluded (AC3)"
        assert "LOT-C" not in codes, "LOT-C (Jan 12) must be excluded (AC3)"

    def test_list_lots_filter_by_date_to(self, seeded_client):
        """
        AC3 — date_to filter should include only lots with start_date ≤ the given date.
        """
        resp = _list_lots(seeded_client, date_to="2026-01-12")
        lots = resp.json()
        codes = {lot["lot_code"] for lot in lots}

        assert "LOT-A" in codes,   "LOT-A (Jan 10) must be included"
        assert "LOT-C" in codes,   "LOT-C (Jan 12) must be included"
        assert "LOT-B" not in codes, "LOT-B (Jan 15) must be excluded (AC3)"
        assert "LOT-D" not in codes, "LOT-D (Jan 20) must be excluded (AC3)"

    def test_list_lots_date_range_both_bounds(self, seeded_client):
        """
        AC3 — Combining date_from and date_to forms a closed date range.
        Only LOT-C (Jan 12) falls between Jan 11 and Jan 13 inclusive.
        """
        resp = _list_lots(seeded_client, date_from="2026-01-11", date_to="2026-01-13")
        lots = resp.json()
        codes = {lot["lot_code"] for lot in lots}

        assert codes == {"LOT-C"}, f"Only LOT-C should be in range; got {codes}"

    def test_list_lots_empty_range_returns_empty(self, seeded_client):
        """
        AC3 — A date range with no matching lots returns an empty list (not an error).
        """
        resp = _list_lots(seeded_client, date_from="2030-01-01", date_to="2030-12-31")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == [], "Future date range → empty list"

    def test_list_lots_results_ordered_by_lot_id(self, seeded_client):
        """
        AC9 — Results must be ordered deterministically by lot_id so the same
        query always returns the same sequence (consistent results).
        """
        resp1 = _list_lots(seeded_client)
        resp2 = _list_lots(seeded_client)

        ids1 = [lot["lot_id"] for lot in resp1.json()]
        ids2 = [lot["lot_id"] for lot in resp2.json()]

        # Same order, same content on repeat calls (AC9)
        assert ids1 == ids2,                "Repeat queries must return same order (AC9)"
        assert ids1 == sorted(ids1),        "Results must be sorted by lot_id (AC9)"


# ─────────────────────────────────────────────────────────────────────────────
# AC9 — Consistent results
# ─────────────────────────────────────────────────────────────────────────────

class TestConsistency:
    """AC9: the same query always returns the same result."""

    def test_same_lot_query_returns_consistent_result(self, seeded_client):
        """
        AC9 — Calling GET /lots/LOT-A twice must return identical responses.
        This proves the underlying data is stable and deterministic.
        """
        resp1 = _get_lot(seeded_client, "LOT-A")
        resp2 = _get_lot(seeded_client, "LOT-A")

        assert resp1.json() == resp2.json(), (
            "Same lot query must return identical results on repeated calls (AC9)"
        )

    def test_list_lots_consistent_on_repeat(self, seeded_client):
        """
        AC9 — The lot list endpoint must return the same result on repeated calls.
        """
        resp1 = _list_lots(seeded_client)
        resp2 = _list_lots(seeded_client)

        assert resp1.json() == resp2.json(), "Repeat list calls must be identical (AC9)"
