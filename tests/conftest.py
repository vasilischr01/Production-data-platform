import os

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

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
