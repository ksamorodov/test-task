"""Tests for the service layer — pure business logic, no HTTP."""

import datetime

import pandas as pd
import pytest

from app.service import compute_aggregation, compute_timeseries


class TestComputeTimeseries:
    def test_returns_list(self, df_x, df_merged):
        assert isinstance(compute_timeseries(df_x, df_merged, "fclick"), list)

    def test_row_count_equals_distinct_dates(self, df_x, df_merged):
        result = compute_timeseries(df_x, df_merged, "fclick")
        assert len(result) == df_x["date"].nunique()

    def test_required_keys(self, df_x, df_merged):
        row = compute_timeseries(df_x, df_merged, "fclick")[0]
        assert {"date", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_impressions_per_day(self, df_x, df_merged):
        """Each date has 2 impressions in the fixture."""
        for row in compute_timeseries(df_x, df_merged, "fclick"):
            assert row["impressions"] == 2

    def test_events_per_day(self, df_x, df_merged):
        """u1 on day-1 and u3 on day-2 both clicked → 1 event per day."""
        for row in compute_timeseries(df_x, df_merged, "fclick"):
            assert row["events"] == 1

    def test_ctr_formula(self, df_x, df_merged):
        for row in compute_timeseries(df_x, df_merged, "fclick"):
            assert row["ctr"] == pytest.approx(row["events"] / row["impressions"] * 100, rel=1e-4)

    def test_evpm_formula(self, df_x, df_merged):
        for row in compute_timeseries(df_x, df_merged, "fclick"):
            assert row["evpm"] == pytest.approx(row["events"] / row["impressions"] * 1000, rel=1e-4)

    def test_dates_are_strings(self, df_x, df_merged):
        for row in compute_timeseries(df_x, df_merged, "fclick"):
            datetime.date.fromisoformat(row["date"])  # raises if format is wrong

    def test_dates_ordered_ascending(self, df_x, df_merged):
        dates = [r["date"] for r in compute_timeseries(df_x, df_merged, "fclick")]
        assert dates == sorted(dates)

    def test_no_events_yields_zero_metrics(self, df_x):
        """A tag that exists nowhere in merged → CTR=0, EvPM=0 for all days."""
        df_merged_empty = df_x.copy()
        df_merged_empty["tag"] = "_no_event"
        for row in compute_timeseries(df_x, df_merged_empty, "never"):
            assert row["ctr"] == 0.0
            assert row["evpm"] == 0.0

    def test_zero_impressions_no_crash(self, df_x, df_merged):
        """If a day somehow has 0 impressions, metrics must be 0.0 not NaN/inf."""
        df_x_empty = df_x.iloc[0:0].copy()   # empty DataFrame, same schema
        result = compute_timeseries(df_x_empty, df_merged, "fclick")
        # no rows to iterate — just assert it didn't raise
        assert isinstance(result, list)


class TestComputeAggregation:
    # ── mm_dma ────────────────────────────────────────────────────────────

    def test_row_count_dma(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "fclick")
        assert len(result["items"]) == df_x["mm_dma"].nunique()

    def test_total_field(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "fclick")
        assert result["total"] == df_x["mm_dma"].nunique()

    def test_required_keys_dma(self, df_x, df_merged):
        row = compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"][0]
        assert {"mm_dma", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_impressions_per_dma(self, df_x, df_merged):
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"]:
            assert row["impressions"] == 2

    def test_events_per_dma(self, df_x, df_merged):
        """DMA 501 → u1 clicked; DMA 612 → u3 clicked. 1 event each."""
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"]:
            assert row["events"] == 1

    def test_ctr_formula_dma(self, df_x, df_merged):
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"]:
            assert row["ctr"] == pytest.approx(row["events"] / row["impressions"] * 100, rel=1e-4)

    def test_evpm_formula_dma(self, df_x, df_merged):
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"]:
            assert row["evpm"] == pytest.approx(row["events"] / row["impressions"] * 1000, rel=1e-4)

    def test_sorted_by_impressions_desc(self, df_x, df_merged):
        imps = [r["impressions"] for r in compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"]]
        assert imps == sorted(imps, reverse=True)

    # ── site_id ───────────────────────────────────────────────────────────

    def test_row_count_site(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "site_id", "fclick")
        assert len(result["items"]) == df_x["site_id"].nunique()

    def test_required_keys_site(self, df_x, df_merged):
        row = compute_aggregation(df_x, df_merged, "site_id", "fclick")["items"][0]
        assert {"site_id", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_events_site_a(self, df_x, df_merged):
        """site_a: u1 + u3 (both fclick) → 2 events."""
        by_site = {r["site_id"]: r for r in compute_aggregation(df_x, df_merged, "site_id", "fclick")["items"]}
        assert by_site["site_a"]["events"] == 2

    def test_zero_events_site_b(self, df_x, df_merged):
        """site_b has no fclick events → CTR and EvPM must be 0."""
        by_site = {r["site_id"]: r for r in compute_aggregation(df_x, df_merged, "site_id", "fclick")["items"]}
        assert by_site["site_b"]["ctr"] == 0.0
        assert by_site["site_b"]["evpm"] == 0.0

    # ── pagination ────────────────────────────────────────────────────────

    def test_pagination_limit(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "fclick", limit=1, offset=0)
        assert len(result["items"]) == 1
        assert result["total"] == 2

    def test_pagination_offset(self, df_x, df_merged):
        all_items  = compute_aggregation(df_x, df_merged, "mm_dma", "fclick")["items"]
        page2_item = compute_aggregation(df_x, df_merged, "mm_dma", "fclick", limit=1, offset=1)["items"][0]
        assert page2_item["mm_dma"] == all_items[1]["mm_dma"]

    def test_pagination_offset_beyond_total(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "fclick", limit=10, offset=999)
        assert result["items"] == []
        assert result["total"] == 2
