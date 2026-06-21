"""
Data access layer.

Reads both CSVs once and exposes the resulting DataFrames to the rest of the
application. The module-level cache means the heavy I/O runs exactly once per
process lifetime regardless of how many requests arrive.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.config import settings


@lru_cache(maxsize=1)
def get_dataframes() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return ``(df_x, df_y, df_merged)``.

    ``df_x``      — impressions (one row per ad view)
    ``df_y``      — events (clicks, registrations, …)
    ``df_merged`` — left-join of df_x onto df_y; rows without an event get
                    tag ``'_no_event'``
    """
    df_x = pd.read_csv(settings.x_csv, parse_dates=["reg_time"])
    df_x["date"] = df_x["reg_time"].dt.date

    df_y = pd.read_csv(settings.y_csv)

    df_merged = df_x.merge(df_y, on="uid", how="left")
    df_merged["tag"] = df_merged["tag"].fillna("_no_event")

    return df_x, df_y, df_merged


def get_event_types() -> list[str]:
    _, df_y, _ = get_dataframes()
    return sorted(df_y["tag"].unique().tolist())
