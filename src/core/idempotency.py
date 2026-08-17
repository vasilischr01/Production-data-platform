import json

from fastapi import HTTPException, status

from src.core.redis import redis_client

IDEMPOTENCY_TTL_SECONDS = 3600


def get_idempotent_response(
    key: str,
) -> dict | None:
    cached = redis_client.get(
        f"idempotency:{key}"
    )

    if cached is None:
        return None

    return json.loads(cached)


def store_idempotent_response(
    key: str,
    response: dict,
) -> None:
    redis_client.setex(
        f"idempotency:{key}",
        IDEMPOTENCY_TTL_SECONDS,
        json.dumps(response),
    )


def ensure_idempotency_key(
    key: str | None,
) -> str:
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    return key