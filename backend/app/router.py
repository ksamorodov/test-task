from fastapi import APIRouter, HTTPException, Query

from app.repository import get_dataframes, get_event_types
from app.schemas import AggregationRow, TimeseriesRow
from app.service import ALLOWED_DIMENSIONS, compute_aggregation, compute_timeseries

router = APIRouter(prefix="/api")


@router.get("/event-types", response_model=list[str])
def event_types() -> list[str]:
    """List all available event tags."""
    return get_event_types()


@router.get("/timeseries", response_model=list[TimeseriesRow])
def timeseries(
    event: str = Query(..., description="Event tag, e.g. 'fclick'"),
) -> list[dict]:
    """Daily CTR and EvPM for the given event type."""
    if event not in get_event_types():
        raise HTTPException(status_code=400, detail=f"Unknown event type: {event!r}")

    df_x, _, df_merged = get_dataframes()
    return compute_timeseries(df_x, df_merged, event)


@router.get("/aggregation")
def aggregation(
    by: str = Query(..., description="Dimension: 'mm_dma' or 'site_id'"),
    event: str = Query(..., description="Event tag, e.g. 'fclick'"),
) -> list[dict]:
    """Aggregated impressions, CTR and EvPM grouped by the chosen dimension."""
    if by not in ALLOWED_DIMENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"'by' must be one of {sorted(ALLOWED_DIMENSIONS)}",
        )
    if event not in get_event_types():
        raise HTTPException(status_code=400, detail=f"Unknown event type: {event!r}")

    df_x, _, df_merged = get_dataframes()
    return compute_aggregation(df_x, df_merged, by, event)
