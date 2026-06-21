from pydantic import BaseModel, Field


class TimeseriesRow(BaseModel):
    date: str
    impressions: int
    events: float
    ctr: float = Field(description="Click-through rate, %")
    evpm: float = Field(description="Events per thousand impressions")


class AggregationRow(BaseModel):
    dimension_value: str | int = Field(alias="dim")
    impressions: int
    events: float
    ctr: float = Field(description="Click-through rate, %")
    evpm: float = Field(description="Events per thousand impressions")
