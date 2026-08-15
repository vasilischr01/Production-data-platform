from datetime import UTC, datetime
from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventCreate(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=128)
    value: float
    unit: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime

    @field_validator("value")
    @classmethod
    def finite_value(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("value must be finite")
        return value

    @field_validator("occurred_at")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)

class BatchEventCreate(BaseModel):
    events: list[EventCreate] = Field(min_length=1, max_length=1000)

class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: str
    source: str
    event_type: str
    value: float
    unit: str | None
    metadata_json: dict[str, Any]
    occurred_at: datetime
    ingested_at: datetime
    processed_at: datetime | None
    processing_status: str
    quality_status: str
    normalized_value: float | None

class BatchIngestResponse(BaseModel):
    accepted: int
    duplicates: int
    event_ids: list[str]
