"""Tests for the HTTP router — status codes, response shape, validation."""

import pytest


class TestEventTypesEndpoint:
    def test_status_200(self, client):
        assert client.get("/api/event-types").status_code == 200

    def test_returns_sorted_tags(self, client):
        data = client.get("/api/event-types").json()
        assert data == sorted(data)

    def test_contains_fclick(self, client):
        assert "fclick" in client.get("/api/event-types").json()


class TestTimeseriesEndpoint:
    def test_status_200(self, client):
        assert client.get("/api/timeseries", params={"event": "fclick"}).status_code == 200

    def test_response_is_list(self, client):
        assert isinstance(client.get("/api/timeseries", params={"event": "fclick"}).json(), list)

    def test_required_fields(self, client):
        row = client.get("/api/timeseries", params={"event": "fclick"}).json()[0]
        assert {"date", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_unknown_event_returns_400(self, client):
        assert client.get("/api/timeseries", params={"event": "ghost"}).status_code == 400

    def test_missing_event_param_returns_422(self, client):
        assert client.get("/api/timeseries").status_code == 422


class TestAggregationEndpoint:
    @pytest.mark.parametrize("by", ["mm_dma", "site_id"])
    def test_status_200(self, client, by):
        assert client.get("/api/aggregation", params={"by": by, "event": "fclick"}).status_code == 200

    @pytest.mark.parametrize("by", ["mm_dma", "site_id"])
    def test_response_is_list(self, client, by):
        assert isinstance(
            client.get("/api/aggregation", params={"by": by, "event": "fclick"}).json(), list
        )

    def test_dma_fields(self, client):
        row = client.get("/api/aggregation", params={"by": "mm_dma", "event": "fclick"}).json()[0]
        assert {"mm_dma", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_site_fields(self, client):
        row = client.get("/api/aggregation", params={"by": "site_id", "event": "fclick"}).json()[0]
        assert {"site_id", "impressions", "events", "ctr", "evpm"} <= row.keys()

    def test_bad_dimension_returns_400(self, client):
        assert client.get("/api/aggregation", params={"by": "uid", "event": "fclick"}).status_code == 400

    def test_unknown_event_returns_400(self, client):
        assert client.get("/api/aggregation", params={"by": "mm_dma", "event": "ghost"}).status_code == 400

    def test_missing_by_returns_422(self, client):
        assert client.get("/api/aggregation", params={"event": "fclick"}).status_code == 422

    def test_missing_event_returns_422(self, client):
        assert client.get("/api/aggregation", params={"by": "mm_dma"}).status_code == 422
