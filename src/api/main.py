from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from src.api.routes_analytics import router as analytics_router
from src.api.routes_auth import router as auth_router
from src.api.routes_events import router as events_router
from src.api.routes_users import router as users_router
from src.core.config import settings
from src.core.logging import configure_logging
from src.db.base import Base
from src.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    yield

configure_logging()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
    }


@app.get("/ready")
def ready():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(auth_router)
app.include_router(users_router)