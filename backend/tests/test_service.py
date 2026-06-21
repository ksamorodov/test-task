"""Tests for the service layer — pure business logic, no HTTP."""

import datetime

import pytest

from app.service import CLICK_TAG, _event_tags, compute_aggregation, compute_timeseries


# ---------------------------------------------------------------------------
# _event_tags helper
# ---------------------------------------------------------------------------

class TestEventTags:
    def test_base_includes_base(self):
        assert "registration" in _event_tags("registration")

    def test_base_includes_view_variant(self):
        assert "vregistration" in _event_tags("registration")

    def test_view_includes_base(self):
        """'vregistration' must normalise to base 'registration'."""
        assert "registration" in _event_tags("vregistration")

    def test_view_includes_view_variant(self):
        assert "vregistration" in _event_tags("vregistration")

    def test_no_double_v_prefix(self):
        """The 'vv'-bug: must not produce 'vvregistration'."""
        assert "vvregistration" not in _event_tags("vregistration")

    def test_base_and_view_produce_same_set(self):
        """Selecting base or view variant yields the identical tag pair."""
        assert _event_tags("registration") == _event_tags("vregistration")

    def test_fclick_never_included(self):
        assert "fclick" not in _event_tags("registration")
        assert "fclick" not in _event_tags("vregistration")

    def test_click_tag_constant(self):
        assert CLICK_TAG == "fclick"


# ---------------------------------------------------------------------------
# compute_timeseries
# ---------------------------------------------------------------------------

class TestComputeTimeseries:
    def test_returns_list(self, df_x, df_merged):
        assert isinstance(compute_timeseries(df_x, df_merged, "registration"), list)

    def test_row_count_equals_distinct_dates(self, df_x, df_merged):
        result = compute_timeseries(df_x, df_merged, "registration")
        assert len(result) == df_x["date"].nunique()

    def test_required_keys(self, df_x, df_merged):
        row = compute_timeseries(df_x, df_merged, "registration")[0]
        assert {"date", "impressions", "clicks", "events", "ctr", "evpm"} <= row.keys()

    def test_impressions_per_day(self, df_x, df_merged):
        """Each date has 3 impressions (u1+u2+u5 on day-1, u3+u4+u6 on day-2)."""
        for row in compute_timeseries(df_x, df_merged, "registration"):
            assert row["impressions"] == 3

    def test_clicks_per_day(self, df_x, df_merged):
        """CTR uses only fclick: u1 on day-1, u3 on day-2 → 1 click each day."""
        for row in compute_timeseries(df_x, df_merged, "registration"):
            assert row["clicks"] == 1

    def test_evpm_sums_base_and_view(self, df_x, df_merged):
        """
        event='registration' → _event_tags → {'registration','vregistration'}
          day-1: u2 → 'registration'   → 1 event
          day-2: u4 → 'vregistration'  → 1 event
        """
        for row in compute_timeseries(df_x, df_merged, "registration"):
            assert row["events"] == 1

    def test_vregistration_gives_same_evpm_as_registration(self, df_x, df_merged):
        """Selecting 'vregistration' normalises to the same base → identical EvPM."""
        rows_base = compute_timeseries(df_x, df_merged, "registration")
        rows_view = compute_timeseries(df_x, df_merged, "vregistration")
        for rb, rv in zip(rows_base, rows_view):
            assert rb["evpm"] == rv["evpm"]
            assert rb["events"] == rv["events"]

    def test_ctr_same_regardless_of_event(self, df_x, df_merged):
        """CTR is always fclick/impressions — selecting a different event must not change it."""
        rows_reg  = compute_timeseries(df_x, df_merged, "registration")
        rows_vreg = compute_timeseries(df_x, df_merged, "vregistration")
        for rr, rv in zip(rows_reg, rows_vreg):
            assert rr["ctr"] == rv["ctr"]

    def test_ctr_formula(self, df_x, df_merged):
        """CTR = 100 * clicks / impressions."""
        for row in compute_timeseries(df_x, df_merged, "registration"):
            assert row["ctr"] == pytest.approx(row["clicks"] / row["impressions"] * 100, rel=1e-4)

    def test_evpm_formula(self, df_x, df_merged):
        """EvPM = 1000 * events / impressions."""
        for row in compute_timeseries(df_x, df_merged, "registration"):
            assert row["evpm"] == pytest.approx(row["events"] / row["impressions"] * 1000, rel=1e-4)

    def test_dates_are_strings(self, df_x, df_merged):
        for row in compute_timeseries(df_x, df_merged, "registration"):
            datetime.date.fromisoformat(row["date"])

    def test_dates_ordered_ascending(self, df_x, df_merged):
        dates = [r["date"] for r in compute_timeseries(df_x, df_merged, "registration")]
        assert dates == sorted(dates)

    def test_unknown_event_yields_zero_evpm(self, df_x, df_merged):
        """An event absent from the data → events=0, evpm=0; CTR still reflects fclick."""
        for row in compute_timeseries(df_x, df_merged, "lead"):
            assert row["events"] == 0
            assert row["evpm"] == 0.0
            assert row["clicks"] == 1   # CTR is independent

    def test_zero_impressions_no_crash(self, df_x, df_merged):
        result = compute_timeseries(df_x.iloc[0:0].copy(), df_merged, "registration")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# compute_aggregation
# ---------------------------------------------------------------------------

class TestComputeAggregation:
    # ── mm_dma ────────────────────────────────────────────────────────────

    def test_row_count_dma(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "registration")
        assert len(result["items"]) == df_x["mm_dma"].nunique()

    def test_total_field(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "registration")
        assert result["total"] == df_x["mm_dma"].nunique()

    def test_required_keys_dma(self, df_x, df_merged):
        """Response must contain exactly ТЗ columns — no internal clicks/events."""
        row = compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"][0]
        assert {"mm_dma", "impressions", "ctr", "evpm"} <= row.keys()
        assert "clicks" not in row
        assert "events" not in row

    def test_impressions_per_dma(self, df_x, df_merged):
        """Each DMA has 3 impressions."""
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"]:
            assert row["impressions"] == 3

    def test_ctr_value_dma(self, df_x, df_merged):
        """1 click / 3 impressions × 100 ≈ 33.3333 % for each DMA."""
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"]:
            assert row["ctr"] == pytest.approx(1 / 3 * 100, rel=1e-4)

    def test_evpm_value_dma(self, df_x, df_merged):
        """
        DMA 501: u2='registration', DMA 612: u4='vregistration'
        → 1 event each / 3 impressions × 1000 ≈ 333.3333 ‰
        """
        for row in compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"]:
            assert row["evpm"] == pytest.approx(1 / 3 * 1000, rel=1e-4)

    def test_vregistration_same_evpm_as_registration(self, df_x, df_merged):
        """Selecting 'vregistration' must yield the same EvPM as 'registration'."""
        rows_base = compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"]
        rows_view = compute_aggregation(df_x, df_merged, "mm_dma", "vregistration")["items"]
        for rb, rv in zip(rows_base, rows_view):
            assert rb["evpm"] == rv["evpm"]

    def test_sorted_by_impressions_desc(self, df_x, df_merged):
        imps = [r["impressions"] for r in
                compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"]]
        assert imps == sorted(imps, reverse=True)

    # ── site_id ───────────────────────────────────────────────────────────

    def test_row_count_site(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "site_id", "registration")
        assert len(result["items"]) == df_x["site_id"].nunique()

    def test_required_keys_site(self, df_x, df_merged):
        row = compute_aggregation(df_x, df_merged, "site_id", "registration")["items"][0]
        assert {"site_id", "impressions", "ctr", "evpm"} <= row.keys()
        assert "clicks" not in row
        assert "events" not in row

    def test_ctr_site_a(self, df_x, df_merged):
        """site_a: 2 clicks, 0 reg events, 3 impressions → CTR=2/3×100, EvPM=0."""
        by_site = {r["site_id"]: r for r in
                   compute_aggregation(df_x, df_merged, "site_id", "registration")["items"]}
        assert by_site["site_a"]["ctr"] == pytest.approx(2 / 3 * 100, rel=1e-4)
        assert by_site["site_a"]["evpm"] == 0.0

    def test_evpm_site_b(self, df_x, df_merged):
        """site_b: 0 clicks, 2 events (reg+vreg), 3 impressions → CTR=0, EvPM=2/3×1000."""
        by_site = {r["site_id"]: r for r in
                   compute_aggregation(df_x, df_merged, "site_id", "registration")["items"]}
        assert by_site["site_b"]["ctr"] == 0.0
        assert by_site["site_b"]["evpm"] == pytest.approx(2 / 3 * 1000, rel=1e-4)

    # ── pagination ────────────────────────────────────────────────────────

    def test_pagination_limit(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "registration", limit=1, offset=0)
        assert len(result["items"]) == 1
        assert result["total"] == 2

    def test_pagination_offset(self, df_x, df_merged):
        all_items  = compute_aggregation(df_x, df_merged, "mm_dma", "registration")["items"]
        page2_item = compute_aggregation(df_x, df_merged, "mm_dma", "registration",
                                         limit=1, offset=1)["items"][0]
        assert page2_item["mm_dma"] == all_items[1]["mm_dma"]

    def test_pagination_offset_beyond_total(self, df_x, df_merged):
        result = compute_aggregation(df_x, df_merged, "mm_dma", "registration",
                                     limit=10, offset=999)
        assert result["items"] == []
        assert result["total"] == 2
