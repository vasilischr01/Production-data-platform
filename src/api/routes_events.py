import logging
from time import perf_counter

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.idempotency import (
    ensure_idempotency_key,
    get_idempotent_response,
    store_idempotent_response,
)
from src.core.metrics import (
    EVENTS_DUPLICATE,
    EVENTS_INGESTED,
    INGEST_LATENCY,
)
from src.db.session import get_db
from src.repositories.events import EventRepository
from src.schemas.event import (
    BatchEventCreate,
    BatchIngestResponse,
    EventCreate,
    EventRead,
)
from src.services.cache import invalidate_analytics_cache
from src.services.processing import process_event
from src.workers.tasks import process_event_task

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/events",
    tags=["events"],
)


def enqueue(
    db: Session,
    event_id: str,
) -> None:
    if settings.process_async:
        process_event_task.delay(
            event_id
        )
    else:
        process_event(
            db,
            event_id,
        )


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    payload: EventCreate,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
    db: Session = Depends(get_db),
):
    key = ensure_idempotency_key(
    idempotency_key
    )

    cached_response = get_idempotent_response(
        key
    )

    if cached_response is not None:
        return EventRead.model_validate(
            cached_response
        )
    start = perf_counter()

    repo = EventRepository(db)

    if repo.get_by_event_id(
        payload.event_id
    ):
        EVENTS_DUPLICATE.inc()

        logger.warning(
            "duplicate_event_rejected",
            extra={
                "event_id": payload.event_id,
            },
        )

        raise HTTPException(
            status_code=409,
            detail="event_id already exists",
        )

    event = repo.create(
        payload
    )

    logger.info(
        "event_ingested",
        extra={
            "event_id": event.event_id,
            "source": event.source,
            "event_type": event.event_type,
        },
    )

    EVENTS_INGESTED.inc()

    INGEST_LATENCY.observe(
        perf_counter() - start
    )

    enqueue(
        db,
        event.event_id,
    )

    invalidate_analytics_cache()

    response = repo.get_by_event_id(
    event.event_id
    )

    response_model = EventRead.model_validate(
        response
    )

    store_idempotent_response(
        key,
        response_model.model_dump(
            mode="json"
        ),
    )

    return response_model


@router.post(
    "/batch",
    response_model=BatchIngestResponse,
)
def create_batch(
    payload: BatchEventCreate,
    db: Session = Depends(get_db),
):
    repo = EventRepository(db)

    ids: list[str] = []
    duplicates = 0

    for item in payload.events:
        if repo.get_by_event_id(
            item.event_id
        ):
            duplicates += 1
            continue

        event = repo.create(
            item
        )

        ids.append(
            event.event_id
        )

        enqueue(
            db,
            event.event_id,
        )

    if ids:
        invalidate_analytics_cache()

    return BatchIngestResponse(
        accepted=len(ids),
        duplicates=duplicates,
        event_ids=ids,
    )


@router.get(
    "",
    response_model=list[EventRead],
)
def list_events(
    source: str | None = None,
    event_type: str | None = None,
    limit: int = Query(
        50,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    return EventRepository(
        db
    ).list(
        source,
        event_type,
        limit,
        offset,
    )


@router.get(
    "/{event_id}",
    response_model=EventRead,
)
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    event = EventRepository(
        db
    ).get_by_event_id(
        event_id
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="event not found",
        )

    return event


@router.post(
    "/{event_id}/process",
    response_model=EventRead,
)
def process_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
):
    event = process_event(
        db,
        event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="event not found",
        )

    invalidate_analytics_cache()

    return event