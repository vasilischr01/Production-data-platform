from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_events: int
    processed_events: int
    pending_events: int
    good_quality_events: int
    bad_quality_events: int
    average_value: float | None

class GroupCount(BaseModel):
    key: str
    count: int
    average_value: float | None
