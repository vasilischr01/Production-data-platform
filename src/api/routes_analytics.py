from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.event import Event
from src.repositories.events import EventRepository
from src.schemas.analytics import AnalyticsSummary, GroupCount

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
def summary(db: Session = Depends(get_db)):
    return EventRepository(db).summary()

@router.get("/by-source", response_model=list[GroupCount])
def by_source(db: Session = Depends(get_db)):
    return EventRepository(db).grouped(Event.source)

@router.get("/by-type", response_model=list[GroupCount])
def by_type(db: Session = Depends(get_db)):
    return EventRepository(db).grouped(Event.event_type)
