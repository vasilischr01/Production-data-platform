from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.event import Event
from src.schemas.event import EventCreate


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_event_id(self, event_id: str):
        return self.db.scalar(select(Event).where(Event.event_id == event_id))

    def create(self, payload: EventCreate):
        event = Event(
            event_id=payload.event_id,
            source=payload.source.strip(),
            event_type=payload.event_type.strip(),
            value=payload.value,
            unit=payload.unit,
            metadata_json=payload.metadata,
            occurred_at=payload.occurred_at,
            ingested_at=datetime.now(UTC),
            processing_status="pending",
            quality_status="unknown",
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list(self, source=None, event_type=None, limit=50, offset=0):
        stmt = select(Event).order_by(Event.occurred_at.desc()).limit(limit).offset(offset)
        if source:
            stmt = stmt.where(Event.source == source)
        if event_type:
            stmt = stmt.where(Event.event_type == event_type)
        return list(self.db.scalars(stmt).all())

    def summary(self):
        total = self.db.scalar(select(func.count()).select_from(Event)) or 0
        processed = self.db.scalar(
            select(func.count()).select_from(Event).where(Event.processing_status == "processed")
        ) or 0
        good = self.db.scalar(
            select(func.count()).select_from(Event).where(Event.quality_status == "good")
        ) or 0
        bad = self.db.scalar(
            select(func.count()).select_from(Event).where(Event.quality_status == "bad")
        ) or 0
        avg = self.db.scalar(select(func.avg(Event.value)))
        return {
            "total_events": total,
            "processed_events": processed,
            "pending_events": total - processed,
            "good_quality_events": good,
            "bad_quality_events": bad,
            "average_value": float(avg) if avg is not None else None,
        }

    def grouped(self, column):
        stmt = select(column, func.count(Event.id), func.avg(Event.value)).group_by(column)
        rows = self.db.execute(stmt).all()
        return [
            {"key": str(k), "count": int(c), "average_value": float(a) if a is not None else None}
            for k, c, a in rows
        ]
