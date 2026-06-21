"""Tests for the HTTP router — status codes, response shape, validation."""

import pytest


class TestEventTypesEndpoint:
    def test_status_200(self, client):
        assert client.get("/api/event-types").status_code == 200

    def test_returns_sorted_tags(self, client):
        data = client.get("/api/event-types").json()
        assert data == sorted(data)

    def test_fclick_not_in_list(self, client):
        """fclick drives CTR internally and must not appear in the event selector."""
        assert "fclick" not in client.get("/api/event-types").json()

    def test_contains_registration(self, client):
        assert "registration" in client.get("/api/event-types").json()


class TestTimeseriesEndpoint:
    def test_status_200(self, client):
        assert client.get("/api/timeseries", params={"event": "registration"}).status_code == 200

    def test_response_is_list(self, client):
        assert isinstance(client.get("/api/timeseries", params={"event": "registration"}).json(), list)

    def test_required_fields(self, client):
        row = client.get("/api/timeseries", params={"event": "registration"}).json()[0]
        assert {"date", "impressions", "clicks", "events", "ctr", "evpm"} <= row.keys()

    def test_unknown_event_returns_400(self, client):
        assert client.get("/api/timeseries", params={"event": "ghost"}).status_code == 400

    def test_missing_event_param_returns_422(self, client):
        assert client.get("/api/timeseries").status_code == 422


class TestAggregationEndpoint:
    @pytest.mark.parametrize("by", ["mm_dma", "site_id"])
    def test_status_200(self, client, by):
        assert client.get("/api/aggregation", params={"by": by, "event": "registration"}).status_code == 200

    @pytest.mark.parametrize("by", ["mm_dma", "site_id"])
    def test_response_shape(self, client, by):
        body = client.get("/api/aggregation", params={"by": by, "event": "registration"}).json()
        assert {"total", "limit", "offset", "items"} <= body.keys()
        assert isinstance(body["items"], list)

    def test_dma_item_fields(self, client):
        """Only ТЗ columns: dimension key + impressions + ctr + evpm."""
        body = client.get("/api/aggregation", params={"by": "mm_dma", "event": "registration"}).json()
        assert {"mm_dma", "impressions", "ctr", "evpm"} == body["items"][0].keys()

    def test_site_item_fields(self, client):
        body = client.get("/api/aggregation", params={"by": "site_id", "event": "registration"}).json()
        assert {"site_id", "impressions", "ctr", "evpm"} == body["items"][0].keys()

    def test_total_equals_distinct_values(self, client):
        body = client.get("/api/aggregation", params={"by": "mm_dma", "event": "registration"}).json()
        assert body["total"] == 2   # fixture has DMA 501 and 612

    def test_pagination_limit(self, client):
        body = client.get("/api/aggregation", params={"by": "mm_dma", "event": "registration", "limit": 1}).json()
        assert len(body["items"]) == 1
        assert body["total"] == 2

    def test_bad_dimension_returns_400(self, client):
        assert client.get("/api/aggregation", params={"by": "uid", "event": "registration"}).status_code == 400

    def test_unknown_event_returns_400(self, client):
        assert client.get("/api/aggregation", params={"by": "mm_dma", "event": "ghost"}).status_code == 400

    def test_missing_by_returns_422(self, client):
        assert client.get("/api/aggregation", params={"event": "registration"}).status_code == 422

    def test_missing_event_returns_422(self, client):
        assert client.get("/api/aggregation", params={"by": "mm_dma"}).status_code == 422

    def test_limit_too_large_returns_422(self, client):
        assert client.get("/api/aggregation", params={"by": "mm_dma", "event": "registration", "limit": 9999}).status_code == 422
