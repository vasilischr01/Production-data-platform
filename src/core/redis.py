from redis import Redis

from src.core.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis() -> Redis:
    return redis_client