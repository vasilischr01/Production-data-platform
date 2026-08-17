import os
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_data_platform.db"
os.environ["PROCESS_ASYNC"] = "false"

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.base import Base
from src.db.session import engine


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_redis():
    with (
        patch(
            "src.api.main.redis_client.ping",
            return_value=True,
        ),
        patch(
            "src.api.routes_analytics.redis_client.get",
            return_value=None,
        ),
        patch(
            "src.api.routes_analytics.redis_client.setex",
            return_value=True,
        ),
        patch(
            "src.services.cache.redis_client.delete",
            return_value=1,
        ),
        patch(
            "src.core.rate_limit.redis_client.incr",
            return_value=1,
        ),
        patch(
            "src.core.rate_limit.redis_client.expire",
            return_value=True,
        ),
        patch(
            "src.core.rate_limit.redis_client.incr",
            return_value=1,
        ),
        patch(
            "src.core.rate_limit.redis_client.expire",
            return_value=True,
        ),
    ):
        yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c