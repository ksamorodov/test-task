from pydantic import BaseModel, Field


class TimeseriesRow(BaseModel):
    date: str
    impressions: int
    clicks: int = Field(description="fclick count — used for CTR")
    events: int = Field(description="event + vevent count — used for EvPM")
    ctr: float = Field(description="100 * clicks / impressions, %")
    evpm: float = Field(description="1000 * events / impressions, ‰")


class AggregationRow(BaseModel):
    dimension_value: str | int = Field(alias="dim")
    impressions: int
    clicks: int = Field(description="fclick count — used for CTR")
    events: int = Field(description="event + vevent count — used for EvPM")
    ctr: float = Field(description="100 * clicks / impressions, %")
    evpm: float = Field(description="1000 * events / impressions, ‰")


class PaginatedAggregation(BaseModel):
    total: int = Field(description="Total number of rows before pagination")
    limit: int
    offset: int
    items: list[dict]
