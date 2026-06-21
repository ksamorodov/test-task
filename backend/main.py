"""
Campaign analytics backend.
Reads interview.X.csv (impressions) and interview.y.csv (events) once at startup,
pre-computes a merged DataFrame, then serves two endpoints:

  GET /api/timeseries?event=<tag>
      Returns daily CTR and EvPM for the chosen event type.

  GET /api/aggregation?by=<mm_dma|site_id>&event=<tag>
      Returns aggregated impressions, CTR and EvPM per dimension value.

Metrics:
  CTR  = events / impressions * 100          (percent)
  EvPM = events / impressions * 1000         (events per 1000 impressions)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent          # project root
DATA_DIR = BASE_DIR / "interview"

X_PATH = DATA_DIR / "interview.X.csv"
Y_PATH = DATA_DIR / "interview.y.csv"

# ---------------------------------------------------------------------------
# Data loading (once at startup)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (df_x, df_y, df_merged)."""
    df_x = pd.read_csv(X_PATH, parse_dates=["reg_time"])
    df_x["date"] = df_x["reg_time"].dt.date

    df_y = pd.read_csv(Y_PATH)

    # Each uid in df_y may appear once per event type; df_x has one row per
    # impression.  We merge on uid to associate every event with its impression.
    df_merged = df_x.merge(df_y, on="uid", how="left")
    df_merged["tag"] = df_merged["tag"].fillna("_no_event")

    return df_x, df_y, df_merged


def get_event_types() -> list[str]:
    _, df_y, _ = load_data()
    return sorted(df_y["tag"].unique().tolist())


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Campaign Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/event-types")
def event_types() -> list[str]:
    """List all available event types (tags)."""
    return get_event_types()


@app.get("/api/timeseries")
def timeseries(
    event: str = Query(..., description="Event tag, e.g. 'fclick'"),
) -> list[dict]:
    """
    Daily CTR and EvPM for the given event type.
    Each row: { date, impressions, events, ctr, evpm }
    """
    df_x, _, df_merged = load_data()

    if event not in get_event_types():
        raise HTTPException(status_code=400, detail=f"Unknown event type: {event!r}")

    # Total daily impressions (from X — independent of event type)
    daily_imp = df_x.groupby("date").size().rename("impressions")

    # Daily events of the requested type
    mask = df_merged["tag"] == event
    daily_ev = df_merged[mask].groupby("date").size().rename("events")

    daily = pd.concat([daily_imp, daily_ev], axis=1).fillna(0).reset_index()
    daily["ctr"]  = (daily["events"] / daily["impressions"] * 100).round(4)
    daily["evpm"] = (daily["events"] / daily["impressions"] * 1000).round(4)
    daily["date"] = daily["date"].astype(str)

    return daily.to_dict(orient="records")


@app.get("/api/aggregation")
def aggregation(
    by: str = Query(..., description="Dimension: 'mm_dma' or 'site_id'"),
    event: str = Query(..., description="Event tag, e.g. 'fclick'"),
) -> list[dict]:
    """
    Aggregated impressions, CTR and EvPM grouped by the chosen dimension.
    Each row: { <dim>, impressions, events, ctr, evpm }
    """
    allowed_dims = {"mm_dma", "site_id"}
    if by not in allowed_dims:
        raise HTTPException(status_code=400, detail=f"'by' must be one of {allowed_dims}")
    if event not in get_event_types():
        raise HTTPException(status_code=400, detail=f"Unknown event type: {event!r}")

    df_x, _, df_merged = load_data()

    # Impressions per dimension value
    imp = df_x.groupby(by).size().rename("impressions")

    # Events per dimension value
    mask = df_merged["tag"] == event
    ev = df_merged[mask].groupby(by).size().rename("events")

    agg = pd.concat([imp, ev], axis=1).fillna(0).reset_index()
    agg["ctr"]  = (agg["events"] / agg["impressions"] * 100).round(4)
    agg["evpm"] = (agg["events"] / agg["impressions"] * 1000).round(4)

    # Sort by impressions descending for readability
    agg = agg.sort_values("impressions", ascending=False)

    return agg.to_dict(orient="records")
