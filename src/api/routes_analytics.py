import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.redis import redis_client
from src.db.session import get_db
from src.models.event import Event
from src.repositories.events import EventRepository
from src.schemas.analytics import AnalyticsSummary, GroupCount
from src.services.cache import ANALYTICS_SUMMARY_CACHE_KEY

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
)


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
)
def summary(
    db: Session = Depends(get_db),
):
    cache_key = ANALYTICS_SUMMARY_CACHE_KEY

    cached_value = redis_client.get(
        cache_key
    )

    if cached_value is not None:
        return AnalyticsSummary.model_validate(
            json.loads(cached_value)
        )

    result = EventRepository(
        db
    ).summary()

    summary_response = (
        AnalyticsSummary.model_validate(
            result
        )
    )

    redis_client.setex(
        cache_key,
        settings.analytics_cache_ttl_seconds,
        summary_response.model_dump_json(),
    )

    return summary_response


@router.get(
    "/by-source",
    response_model=list[GroupCount],
)
def by_source(
    db: Session = Depends(get_db),
):
    return EventRepository(
        db
    ).grouped(
        Event.source
    )


@router.get(
    "/by-type",
    response_model=list[GroupCount],
)
def by_type(
    db: Session = Depends(get_db),
):
    return EventRepository(
        db
    ).grouped(
        Event.event_type
    )