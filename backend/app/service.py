"""
Business logic layer.

All metric calculations live here. Functions receive raw DataFrames from the
repository and return plain dicts ready to be validated by Pydantic schemas in
the router. No HTTP concerns (FastAPI, Request, Response) belong here.

Metrics
-------
CTR  = events / impressions * 100    (percent)
EvPM = events / impressions * 1000   (events per thousand impressions)
"""

from __future__ import annotations

import pandas as pd

ALLOWED_DIMENSIONS = frozenset({"mm_dma", "site_id"})


def compute_timeseries(
    df_x: pd.DataFrame,
    df_merged: pd.DataFrame,
    event: str,
) -> list[dict]:
    """Return daily CTR and EvPM for *event*."""
    daily_imp = df_x.groupby("date").size().rename("impressions")

    mask = df_merged["tag"] == event
    daily_ev = df_merged.loc[mask].groupby("date").size().rename("events")

    daily = (
        pd.concat([daily_imp, daily_ev], axis=1)
        .fillna(0)
        .reset_index()
    )
    daily["ctr"]  = (daily["events"] / daily["impressions"] * 100).round(4)
    daily["evpm"] = (daily["events"] / daily["impressions"] * 1000).round(4)
    daily["date"] = daily["date"].astype(str)

    return daily.to_dict(orient="records")


def compute_aggregation(
    df_x: pd.DataFrame,
    df_merged: pd.DataFrame,
    by: str,
    event: str,
) -> list[dict]:
    """Return per-*by*-value impressions, CTR and EvPM for *event*."""
    imp = df_x.groupby(by).size().rename("impressions")

    mask = df_merged["tag"] == event
    ev = df_merged.loc[mask].groupby(by).size().rename("events")

    agg = (
        pd.concat([imp, ev], axis=1)
        .fillna(0)
        .reset_index()
        .sort_values("impressions", ascending=False)
    )
    agg["ctr"]  = (agg["events"] / agg["impressions"] * 100).round(4)
    agg["evpm"] = (agg["events"] / agg["impressions"] * 1000).round(4)

    return agg.to_dict(orient="records")
