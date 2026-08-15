from src.db.session import SessionLocal
from src.services.processing import process_event
from src.workers.celery_app import celery_app


@celery_app.task(name="process_event")
def process_event_task(event_id: str):
    db = SessionLocal()
    try:
        event = process_event(db, event_id)
        return {
            "event_id": event_id,
            "processed": event is not None,
        }
    finally:
        db.close()