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

import numpy as np
import pandas as pd

ALLOWED_DIMENSIONS = frozenset({"mm_dma", "site_id"})


def _safe_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute CTR and EvPM in-place, guarding against zero impressions.

    Pandas produces NaN when dividing 0/0 and inf when dividing n/0.
    Both are not valid JSON values, so we replace them with 0.0 explicitly.
    """
    ratio = df["events"] / df["impressions"]
    ratio = ratio.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["ctr"]  = (ratio * 100).round(4)
    df["evpm"] = (ratio * 1000).round(4)
    return df


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
    daily = _safe_metrics(daily)
    daily["date"] = daily["date"].astype(str)

    return daily.to_dict(orient="records")


def compute_aggregation(
    df_x: pd.DataFrame,
    df_merged: pd.DataFrame,
    by: str,
    event: str,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Return paginated per-*by*-value impressions, CTR and EvPM for *event*.

    Returns a dict with keys: total, limit, offset, items.
    """
    imp = df_x.groupby(by).size().rename("impressions")

    mask = df_merged["tag"] == event
    ev = df_merged.loc[mask].groupby(by).size().rename("events")

    agg = (
        pd.concat([imp, ev], axis=1)
        .fillna(0)
        .reset_index()
        .sort_values("impressions", ascending=False)
    )
    agg = _safe_metrics(agg)
    # cast events to int after safe division (fillna(0) makes it float)
    agg["events"] = agg["events"].astype(int)

    total = len(agg)
    page = agg.iloc[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": page.to_dict(orient="records"),
    }
