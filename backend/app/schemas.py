from pydantic import BaseModel, Field


class TimeseriesRow(BaseModel):
    date: str
    impressions: int
    events: int
    ctr: float = Field(description="Click-through rate, %")
    evpm: float = Field(description="Events per thousand impressions")


class AggregationRow(BaseModel):
    dimension_value: str | int = Field(alias="dim")
    impressions: int
    events: int
    ctr: float = Field(description="Click-through rate, %")
    evpm: float = Field(description="Events per thousand impressions")


class PaginatedAggregation(BaseModel):
    total: int = Field(description="Total number of rows before pagination")
    limit: int
    offset: int
    items: list[dict]
