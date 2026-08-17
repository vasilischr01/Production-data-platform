from fastapi import HTTPException, Request, status

from src.core.redis import redis_client


def enforce_rate_limit(
    request: Request,
    *,
    limit: int,
    window_seconds: int,
    scope: str,
) -> None:
    client_host = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    key = (
        f"rate-limit:{scope}:{client_host}"
    )

    current = redis_client.incr(key)

    if current == 1:
        redis_client.expire(
            key,
            window_seconds,
        )

    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(
                    window_seconds
                )
            },
        )