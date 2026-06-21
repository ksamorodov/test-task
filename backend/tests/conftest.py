"""Shared pytest fixtures."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Factory for synthetic DataFrames — called inside fixtures, not at import time.
#
# 6 impressions: 2 dates × 2 DMA codes × 2 sites, richer event mix:
#   u1: 2021-07-21, DMA 501, site_a  → fclick
#   u2: 2021-07-21, DMA 501, site_b  → registration
#   u3: 2021-07-22, DMA 612, site_a  → fclick
#   u4: 2021-07-22, DMA 612, site_b  → vregistration
#   u5: 2021-07-21, DMA 501, site_a  → (no event)
#   u6: 2021-07-22, DMA 612, site_b  → (no event)
#
# Expected results for event='registration':
#   EvPM counts both 'registration' (u2) and 'vregistration' (u4) → 2 events
#   CTR  counts only fclick (u1, u3)                               → 2 clicks
# ---------------------------------------------------------------------------

def _make_dataframes():
    df_x = pd.DataFrame(
        {
            "uid": ["u1", "u2", "u3", "u4", "u5", "u6"],
            "reg_time": pd.to_datetime([
                "2021-07-21 10:00", "2021-07-21 11:00",
                "2021-07-22 09:00", "2021-07-22 12:00",
                "2021-07-21 13:00", "2021-07-22 14:00",
            ]),
            "mm_dma": [501, 501, 612, 612, 501, 612],
            "site_id": ["site_a", "site_b", "site_a", "site_b", "site_a", "site_b"],
        }
    )
    df_x["date"] = df_x["reg_time"].dt.date

    df_y = pd.DataFrame({
        "uid": ["u1", "u2", "u3", "u4"],
        "tag": ["fclick", "registration", "fclick", "vregistration"],
    })

    df_merged = df_x.merge(df_y, on="uid", how="left")
    df_merged["tag"] = df_merged["tag"].fillna("_no_event")

    return df_x, df_y, df_merged


@pytest.fixture()
def dataframes():
    """Fresh synthetic DataFrames per test — no shared mutable state."""
    return _make_dataframes()


# Convenience aliases consumed by test_service.py
@pytest.fixture()
def df_x(dataframes):
    return dataframes[0]


@pytest.fixture()
def df_merged(dataframes):
    return dataframes[2]


@pytest.fixture(autouse=True)
def patch_repository(monkeypatch, dataframes):
    """Patch both the repository module and its re-imports in router.py."""
    df_x, df_y, df_merged = dataframes

    # Single source of truth: patch app.repository, then make router
    # point at the already-patched name via the same target.
    monkeypatch.setattr("app.repository.get_dataframes", lambda: (df_x, df_y, df_merged))
    monkeypatch.setattr("app.repository.get_event_types", lambda: ["registration"])
    # router imported these names at module load time — patch those bindings too
    monkeypatch.setattr("app.router.get_dataframes", lambda: (df_x, df_y, df_merged))
    monkeypatch.setattr("app.router.get_event_types", lambda: ["registration"])


@pytest.fixture()
def client():
    return TestClient(app)
