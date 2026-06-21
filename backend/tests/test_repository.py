"""Tests for the repository layer (get_event_types)."""

from app.repository import get_event_types


class TestGetEventTypes:
    def test_returns_list(self):
        assert isinstance(get_event_types(), list)

    def test_returns_sorted(self):
        result = get_event_types()
        assert result == sorted(result)

    def test_fclick_excluded(self):
        """fclick is used internally for CTR, must not appear in the event selector."""
        assert "fclick" not in get_event_types()

    def test_no_view_through_variants(self):
        """View-through variants (vXxx) must be stripped — only base names returned."""
        for tag in get_event_types():
            assert not tag.startswith("v"), f"view-through variant leaked: {tag!r}"

    def test_contains_registration(self):
        """Fixture has both 'registration' and 'vregistration' → base 'registration' expected."""
        assert "registration" in get_event_types()
