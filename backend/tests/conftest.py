"""Shared pytest fixtures."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import main as app_module
from app.main import app
from app.repository import get_dataframes, get_event_types


# ---------------------------------------------------------------------------
# Synthetic DataFrames
#
# 4 impressions: 2 dates × 2 DMA codes × 2 sites
#   u1: 2021-07-21, DMA 501, site_a  → fclick
#   u2: 2021-07-21, DMA 501, site_b  → (no event)
#   u3: 2021-07-22, DMA 612, site_a  → fclick
#   u4: 2021-07-22, DMA 612, site_b  → (no event)
# ---------------------------------------------------------------------------

DF_X = pd.DataFrame(
    {
        "uid": ["u1", "u2", "u3", "u4"],
        "reg_time": pd.to_datetime(
            ["2021-07-21 10:00", "2021-07-21 11:00", "2021-07-22 09:00", "2021-07-22 12:00"]
        ),
        "mm_dma": [501, 501, 612, 612],
        "site_id": ["site_a", "site_b", "site_a", "site_b"],
    }
)
DF_X["date"] = DF_X["reg_time"].dt.date

DF_Y = pd.DataFrame({"uid": ["u1", "u3"], "tag": ["fclick", "fclick"]})

DF_MERGED = DF_X.merge(DF_Y, on="uid", how="left")
DF_MERGED["tag"] = DF_MERGED["tag"].fillna("_no_event")


@pytest.fixture(autouse=True)
def patch_repository(monkeypatch):
    """Replace repository functions with synthetic data for every test."""
    monkeypatch.setattr("app.repository.get_dataframes", lambda: (DF_X, DF_Y, DF_MERGED))
    monkeypatch.setattr("app.router.get_dataframes", lambda: (DF_X, DF_Y, DF_MERGED))
    monkeypatch.setattr("app.repository.get_event_types", lambda: ["fclick"])
    monkeypatch.setattr("app.router.get_event_types", lambda: ["fclick"])


@pytest.fixture()
def client():
    return TestClient(app)
