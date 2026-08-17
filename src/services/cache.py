from src.core.redis import redis_client

ANALYTICS_SUMMARY_CACHE_KEY = (
    "analytics:summary:v1"
)


def invalidate_analytics_cache() -> None:
    redis_client.delete(
        ANALYTICS_SUMMARY_CACHE_KEY
    )