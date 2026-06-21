"""
Business logic layer.

All metric calculations live here. Functions receive raw DataFrames from the
repository and return plain dicts ready to be validated by Pydantic schemas in
the router. No HTTP concerns (FastAPI, Request, Response) belong here.

Metrics (per ТЗ)
----------------
CTR  = 100  * fclick_count / impression_count  %
         fclick_count — rows where tag == 'fclick', always, regardless of the
                        selected event type. Never changes.

EvPM = 1000 * event_count  / impression_count  ‰
         event_count — rows where tag IN {base_event, 'v' + base_event}.
                       The user may select either the direct or the view-through
                       variant; both are normalised to the same base before
                       matching, so 'registration' and 'vregistration' produce
                       the same EvPM (sum of both variants).
                       Example: event='vregistration' → base='registration'
                                → counts tag=='registration' + tag=='vregistration'.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ALLOWED_DIMENSIONS = frozenset({"mm_dma", "site_id"})

# The only tag that counts as a "click" for CTR purposes.
CLICK_TAG = "fclick"


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide two Series, replacing NaN / ±inf with 0.0."""
    result = numerator / denominator
    return result.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _event_tags(event: str) -> frozenset[str]:
    """Return the pair of raw tags that contribute to EvPM for *event*.

    The user may select either the direct or view-through variant of an event.
    We normalise to the base name first, then always return both:

        'registration'  → base='registration'  → {'registration', 'vregistration'}
        'vregistration' → base='registration'  → {'registration', 'vregistration'}

    This avoids the 'vv'-prefix bug that would arise from naïvely doing
    f"v{event}" when event already starts with 'v'.
    """
    base = event[1:] if event.startswith("v") else event
    return frozenset({base, f"v{base}"})


def compute_timeseries(
    df_x: pd.DataFrame,
    df_merged: pd.DataFrame,
    event: str,
) -> list[dict]:
    """Return daily CTR and EvPM.

    CTR  = 100  * fclick_count / impressions  — always fclick only, never changes.
    EvPM = 1000 * event_count  / impressions  — event_count = tag IN _event_tags(event),
                                                i.e. both base and view-through variant.
    """
    daily_imp = df_x.groupby("date").size().rename("impressions")

    click_mask = df_merged["tag"] == CLICK_TAG
    daily_clicks = df_merged.loc[click_mask].groupby("date").size().rename("clicks")

    ev_mask = df_merged["tag"].isin(_event_tags(event))
    daily_ev = df_merged.loc[ev_mask].groupby("date").size().rename("events")

    daily = (
        pd.concat([daily_imp, daily_clicks, daily_ev], axis=1)
        .fillna(0)
        .reset_index()
    )
    daily["ctr"]  = (_safe_divide(daily["clicks"], daily["impressions"]) * 100).round(4)
    daily["evpm"] = (_safe_divide(daily["events"], daily["impressions"]) * 1000).round(4)
    daily["clicks"] = daily["clicks"].astype(int)
    daily["events"] = daily["events"].astype(int)
    daily["date"]   = daily["date"].astype(str)

    return daily.to_dict(orient="records")


def compute_aggregation(
    df_x: pd.DataFrame,
    df_merged: pd.DataFrame,
    by: str,
    event: str,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Return paginated per-*by*-value impressions, CTR and EvPM.

    CTR  = 100  * fclick_count / impressions  — always fclick only, never changes.
    EvPM = 1000 * event_count  / impressions  — event_count = tag IN _event_tags(event),
                                                i.e. both base and view-through variant.

    Response columns (per ТЗ): dimension key, impressions, ctr, evpm.
    Returns a dict with keys: total, limit, offset, items.
    """
    imp = df_x.groupby(by).size().rename("impressions")

    clicks = (
        df_merged.loc[df_merged["tag"] == CLICK_TAG]
        .groupby(by).size().rename("clicks")
    )
    ev = (
        df_merged.loc[df_merged["tag"].isin(_event_tags(event))]
        .groupby(by).size().rename("events")
    )

    agg = (
        pd.concat([imp, clicks, ev], axis=1)
        .fillna(0)
        .reset_index()
        .sort_values("impressions", ascending=False)
    )
    agg["ctr"]  = (_safe_divide(agg["clicks"], agg["impressions"]) * 100).round(4)
    agg["evpm"] = (_safe_divide(agg["events"], agg["impressions"]) * 1000).round(4)

    output_cols = [by, "impressions", "ctr", "evpm"]
    total = len(agg)
    page = agg[output_cols].iloc[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": page.to_dict(orient="records"),
    }
