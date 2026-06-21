"""Tests for the service layer — pure business logic, no HTTP."""

import pandas as pd
import pytest

from app.service import compute_aggregation, compute_timeseries
from tests.conftest import DF_MERGED, DF_X


class TestComputeTimeseries:
    def test_returns_list(self):
        result = compute_timeseries(DF_X, DF_MERGED, "fclick")
        assert isinstance(result, list)

    def test_row_count_equals_distinct_dates(self):
        result = compute_timeseries(DF_X, DF_MERGED, "fclick")
        assert len(result) == DF_X["date"].nunique()

    def test_required_keys(self):
        row = compute_timeseries(DF_X, DF_MERGED, "fclick")[0]
        assert {"date", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_impressions_per_day(self):
        """Each date has 2 impressions in the fixture."""
        for row in compute_timeseries(DF_X, DF_MERGED, "fclick"):
            assert row["impressions"] == 2

    def test_events_per_day(self):
        """u1 on day-1 and u3 on day-2 both clicked → 1 event per day."""
        for row in compute_timeseries(DF_X, DF_MERGED, "fclick"):
            assert row["events"] == 1.0

    def test_ctr_formula(self):
        for row in compute_timeseries(DF_X, DF_MERGED, "fclick"):
            assert row["ctr"] == pytest.approx(row["events"] / row["impressions"] * 100, rel=1e-4)

    def test_evpm_formula(self):
        for row in compute_timeseries(DF_X, DF_MERGED, "fclick"):
            assert row["evpm"] == pytest.approx(row["events"] / row["impressions"] * 1000, rel=1e-4)

    def test_dates_are_strings(self):
        import datetime
        for row in compute_timeseries(DF_X, DF_MERGED, "fclick"):
            datetime.date.fromisoformat(row["date"])  # raises if format is wrong

    def test_dates_ordered_ascending(self):
        dates = [r["date"] for r in compute_timeseries(DF_X, DF_MERGED, "fclick")]
        assert dates == sorted(dates)

    def test_no_events_yields_zero_metrics(self):
        """A tag that exists nowhere in merged → CTR=0, EvPM=0 for all days."""
        # Build a merged df where no row has tag "never"
        df_merged_empty = DF_X.copy()
        df_merged_empty["tag"] = "_no_event"
        for row in compute_timeseries(DF_X, df_merged_empty, "never"):
            assert row["ctr"] == 0.0
            assert row["evpm"] == 0.0


class TestComputeAggregation:
    # ── mm_dma ────────────────────────────────────────────────────────────

    def test_row_count_dma(self):
        result = compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick")
        assert len(result) == DF_X["mm_dma"].nunique()

    def test_required_keys_dma(self):
        row = compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick")[0]
        assert {"mm_dma", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_impressions_per_dma(self):
        for row in compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick"):
            assert row["impressions"] == 2

    def test_events_per_dma(self):
        """DMA 501 → u1 clicked; DMA 612 → u3 clicked. 1 event each."""
        for row in compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick"):
            assert row["events"] == 1.0

    def test_ctr_formula_dma(self):
        for row in compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick"):
            assert row["ctr"] == pytest.approx(row["events"] / row["impressions"] * 100, rel=1e-4)

    def test_evpm_formula_dma(self):
        for row in compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick"):
            assert row["evpm"] == pytest.approx(row["events"] / row["impressions"] * 1000, rel=1e-4)

    def test_sorted_by_impressions_desc(self):
        imps = [r["impressions"] for r in compute_aggregation(DF_X, DF_MERGED, "mm_dma", "fclick")]
        assert imps == sorted(imps, reverse=True)

    # ── site_id ───────────────────────────────────────────────────────────

    def test_row_count_site(self):
        result = compute_aggregation(DF_X, DF_MERGED, "site_id", "fclick")
        assert len(result) == DF_X["site_id"].nunique()

    def test_required_keys_site(self):
        row = compute_aggregation(DF_X, DF_MERGED, "site_id", "fclick")[0]
        assert {"site_id", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_events_site_a(self):
        """site_a: u1 + u3 (both fclick) → 2 events."""
        by_site = {r["site_id"]: r for r in compute_aggregation(DF_X, DF_MERGED, "site_id", "fclick")}
        assert by_site["site_a"]["events"] == 2.0

    def test_zero_events_site_b(self):
        """site_b has no fclick events → CTR and EvPM must be 0."""
        by_site = {r["site_id"]: r for r in compute_aggregation(DF_X, DF_MERGED, "site_id", "fclick")}
        assert by_site["site_b"]["ctr"] == 0.0
        assert by_site["site_b"]["evpm"] == 0.0
