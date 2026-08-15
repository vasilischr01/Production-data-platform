from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.core.metrics import EVENTS_PROCESSED
from src.repositories.events import EventRepository
from src.services.quality import assess_quality, normalize_value


def process_event(db: Session, event_id: str):
    repo = EventRepository(db)
    event = repo.get_by_event_id(event_id)
    if event is None:
        return None
    event.quality_status = assess_quality(event.value, event.source, event.event_type)
    event.normalized_value = normalize_value(event.value)
    event.processing_status = "processed"
    event.processed_at = datetime.now(UTC)
    db.add(event)
    db.commit()
    db.refresh(event)
    EVENTS_PROCESSED.labels(
    quality_status=event.quality_status
    ).inc()
    return event
