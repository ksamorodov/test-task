"""Tests for the repository layer (get_event_types)."""

from app.repository import get_event_types


class TestGetEventTypes:
    def test_returns_list(self):
        assert isinstance(get_event_types(), list)

    def test_returns_sorted(self):
        result = get_event_types()
        assert result == sorted(result)

    def test_contains_fclick(self):
        assert "fclick" in get_event_types()
