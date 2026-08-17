import json
from unittest.mock import patch

from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.db.session import engine
from src.models.user import User, UserRole


def event(event_id="evt-1", source="machine-a", event_type="temperature", value=72.4):
    return {
        "event_id": event_id,
        "source": source,
        "event_type": event_type,
        "value": value,
        "unit": "celsius",
        "metadata": {"factory": "plant-1"},
        "occurred_at": "2026-08-14T09:00:00Z",
    }

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_create_get_and_duplicate(client):
    r = client.post(
        "/api/v1/events",
        json=event(),
        headers={
            "Idempotency-Key": "test-create-event-1",
        },
    )
    assert r.status_code == 201
    assert r.json()["processing_status"] == "processed"

    r = client.get("/api/v1/events/evt-1")
    assert r.status_code == 200

    r = client.post(
        "/api/v1/events",
        json=event(),
        headers={
            "Idempotency-Key": "test-duplicate-event-2",
        },
    )
    assert r.status_code == 409

def test_batch_and_filter(client):
    payload = {
        "events": [
            event("evt-1", "machine-a"),
            event("evt-2", "machine-b", value=50),
            event("evt-2", "machine-b", value=50),
        ]
    }
    r = client.post("/api/v1/events/batch", json=payload)
    assert r.status_code == 200
    assert r.json()["accepted"] == 2
    assert r.json()["duplicates"] == 1

    r = client.get("/api/v1/events?source=machine-a")
    assert r.status_code == 200
    assert len(r.json()) == 1

def test_analytics(client):
    client.post(
        "/api/v1/events",
        json=event("1", "machine-a", "temperature", 10),
        headers={
            "Idempotency-Key": "analytics-event-1",
        },
    )
    client.post(
        "/api/v1/events",
        json=event("2", "machine-a", "vibration", 20),
        headers={
            "Idempotency-Key": "analytics-event-2",
        },
    )
    client.post(
        "/api/v1/events",
        json=event("3", "machine-b", "temperature", 30),
        headers={
            "Idempotency-Key": "analytics-event-3",
        },
    )

    r = client.get("/api/v1/analytics/summary")
    assert r.status_code == 200
    assert r.json()["total_events"] == 3
    assert r.json()["average_value"] == 20.0

    r = client.get("/api/v1/analytics/by-source")
    rows = {x["key"]: x for x in r.json()}
    assert rows["machine-a"]["count"] == 2
    assert rows["machine-b"]["count"] == 1

def test_async_event_processing_flow(client):
    payload = {
        "event_id": "evt-async-001",
        "source": "machine-async",
        "event_type": "temperature",
        "value": 33.3,
        "unit": "celsius",
        "metadata": {
            "factory": "plant-async"
        },
        "occurred_at": "2026-08-14T10:20:00Z",
    }

    with patch("src.api.routes_events.settings.process_async", True), \
         patch("src.api.routes_events.process_event_task.delay") as mock_delay:

        response = client.post(
            "/api/v1/events",
            json=payload,
            headers={
                "Idempotency-Key": "async-event-1",
            },
        )

        assert response.status_code == 201
        assert response.json()["processing_status"] == "pending"

        mock_delay.assert_called_once_with("evt-async-001")

    process_response = client.post(
        "/api/v1/events/evt-async-001/process"
    )

    assert process_response.status_code == 200
    assert process_response.json()["processing_status"] == "processed"
    assert process_response.json()["quality_status"] == "good"
    assert process_response.json()["normalized_value"] is not None

def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "user@example.com"
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert "hashed_password" not in body


def test_duplicate_registration_is_rejected(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_returns_access_token(client):
    payload = {
        "email": "login@example.com",
        "password": "StrongPassword123!",
    }

    client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    response = client.post(
        "/api/v1/auth/login",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong-password@example.com",
            "password": "CorrectPassword123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-password@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_current_user_endpoint(client):
    credentials = {
        "email": "me@example.com",
        "password": "StrongPassword123!",
    }

    client.post(
        "/api/v1/auth/register",
        json=credentials,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == "me@example.com"
    assert body["role"] == "user"


def test_current_user_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401

def test_regular_user_cannot_list_users(
    client,
):
    credentials = {
        "email": "regular@example.com",
        "password": "StrongPassword123!",
    }

    client.post(
        "/api/v1/auth/register",
        json=credentials,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403

def test_admin_can_list_users(client):
    with Session(engine) as db:
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password(
                "AdminPassword123!"
            ),
            role=UserRole.ADMIN.value,
            is_active=True,
        )

        db.add(admin)
        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, dict)
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 1
    assert body["pages"] == 1

    assert len(body["items"]) == 1
    assert body["items"][0]["email"] == "admin@example.com"
    assert body["items"][0]["role"] == UserRole.ADMIN.value

def test_admin_users_pagination(client):
    with Session(engine) as db:
        for index in range(5):
            db.add(
                User(
                    email=f"user{index}@example.com",
                    hashed_password=hash_password(
                        "Password123!"
                    ),
                    role=UserRole.USER.value,
                    is_active=True,
                )
            )

        admin = User(
            email="admin-pagination@example.com",
            hashed_password=hash_password(
                "AdminPassword123!"
            ),
            role=UserRole.ADMIN.value,
            is_active=True,
        )

        db.add(admin)
        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin-pagination@example.com",
            "password": "AdminPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/admin/users?page=2&page_size=2",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total"] == 6
    assert body["pages"] == 3
    assert len(body["items"]) == 2


def test_admin_users_role_filter(client):
    with Session(engine) as db:
        db.add_all(
            [
                User(
                    email="admin-filter@example.com",
                    hashed_password=hash_password(
                        "AdminPassword123!"
                    ),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
                User(
                    email="user-filter@example.com",
                    hashed_password=hash_password(
                        "Password123!"
                    ),
                    role=UserRole.USER.value,
                    is_active=True,
                ),
            ]
        )

        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin-filter@example.com",
            "password": "AdminPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/admin/users?role=admin",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["role"] == UserRole.ADMIN.value


def test_admin_users_email_search(client):
    with Session(engine) as db:
        db.add_all(
            [
                User(
                    email="alpha@example.com",
                    hashed_password=hash_password(
                        "Password123!"
                    ),
                    role=UserRole.USER.value,
                    is_active=True,
                ),
                User(
                    email="beta@test.com",
                    hashed_password=hash_password(
                        "Password123!"
                    ),
                    role=UserRole.USER.value,
                    is_active=True,
                ),
                User(
                    email="admin-search@example.com",
                    hashed_password=hash_password(
                        "AdminPassword123!"
                    ),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
            ]
        )

        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin-search@example.com",
            "password": "AdminPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/admin/users?email=test.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["email"] == "beta@test.com"


def test_admin_users_sorting(client):
    with Session(engine) as db:
        db.add_all(
            [
                User(
                    email="zeta@example.com",
                    hashed_password=hash_password(
                        "Password123!"
                    ),
                    role=UserRole.USER.value,
                    is_active=True,
                ),
                User(
                    email="alpha@example.com",
                    hashed_password=hash_password(
                        "Password123!"
                    ),
                    role=UserRole.USER.value,
                    is_active=True,
                ),
                User(
                    email="admin-sort@example.com",
                    hashed_password=hash_password(
                        "AdminPassword123!"
                    ),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
            ]
        )

        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin-sort@example.com",
            "password": "AdminPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/admin/users?sort_by=email&sort_order=asc",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    emails = [
        item["email"]
        for item in response.json()["items"]
    ]

    assert emails == sorted(emails)

def test_request_id_is_generated(
    client,
):
    response = client.get(
        "/health"
    )

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers[
        "X-Request-ID"
    ]


def test_request_id_is_preserved(
    client,
):
    request_id = "test-request-id-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id
        },
    )

    assert response.status_code == 200
    assert (
        response.headers[
            "X-Request-ID"
        ]
        == request_id
    )

def test_ready_checks_dependencies(
    client,
):
    response = client.get(
        "/ready"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready"
    }

def test_analytics_summary_cache_miss(
    client,
):
    cached_summary = {
        "total_events": 0,
        "processed_events": 0,
        "pending_events": 0,
        "good_quality_events": 0,
        "bad_quality_events": 0,
        "average_value": None,
    }

    with (
        patch(
            "src.api.routes_analytics.redis_client.get",
            return_value=None,
        ) as mock_get,
        patch(
            "src.api.routes_analytics.redis_client.setex",
            return_value=True,
        ) as mock_setex,
        patch(
            "src.api.routes_analytics.EventRepository.summary",
            return_value=cached_summary,
        ) as mock_summary,
    ):
        response = client.get(
            "/api/v1/analytics/summary"
        )

    assert response.status_code == 200
    assert response.json() == cached_summary

    mock_get.assert_called_once_with(
        "analytics:summary:v1"
    )

    mock_summary.assert_called_once()

    mock_setex.assert_called_once()


def test_analytics_summary_cache_hit(
    client,
):
    cached_summary = {
        "total_events": 12,
        "processed_events": 8,
        "pending_events": 4,
        "good_quality_events": 7,
        "bad_quality_events": 1,
        "average_value": 42.5,
    }

    with (
        patch(
            "src.api.routes_analytics.redis_client.get",
            return_value=json.dumps(
                cached_summary
            ),
        ) as mock_get,
        patch(
            "src.api.routes_analytics.redis_client.setex",
        ) as mock_setex,
        patch(
            "src.api.routes_analytics.EventRepository.summary",
        ) as mock_summary,
    ):
        response = client.get(
            "/api/v1/analytics/summary"
        )

    assert response.status_code == 200
    assert response.json() == cached_summary

    mock_get.assert_called_once_with(
        "analytics:summary:v1"
    )

    mock_summary.assert_not_called()
    mock_setex.assert_not_called()

def test_create_event_invalidates_analytics_cache(
    client,
):
    payload = {
        "event_id": "event-cache-1",
        "source": "sensor-a",
        "event_type": "temperature",
        "value": 21.5,
        "unit": "celsius",
        "metadata_json": {},
        "occurred_at": "2026-08-17T10:00:00Z",
    }

    with patch(
        "src.api.routes_events.invalidate_analytics_cache"
    ) as mock_invalidate:
        response = client.post(
            "/api/v1/events",
            json=payload,
            headers={
                "Idempotency-Key": "cache-invalidation-event-1",
            },
        )

    assert response.status_code == 201
    mock_invalidate.assert_called_once()


def test_batch_event_creation_invalidates_cache_once(
    client,
):
    payload = {
        "events": [
            {
                "event_id": "batch-cache-1",
                "source": "sensor-a",
                "event_type": "temperature",
                "value": 20.0,
                "unit": "celsius",
                "metadata_json": {},
                "occurred_at": "2026-08-17T10:00:00Z",
            },
            {
                "event_id": "batch-cache-2",
                "source": "sensor-b",
                "event_type": "temperature",
                "value": 22.0,
                "unit": "celsius",
                "metadata_json": {},
                "occurred_at": "2026-08-17T10:01:00Z",
            },
        ]
    }

    with patch(
        "src.api.routes_events.invalidate_analytics_cache"
    ) as mock_invalidate:
        response = client.post(
            "/api/v1/events/batch",
            json=payload,
        )

    assert response.status_code == 200
    assert response.json()["accepted"] == 2
    mock_invalidate.assert_called_once()


def test_duplicate_only_batch_does_not_invalidate_cache(
    client,
):
    event = {
        "event_id": "duplicate-cache-1",
        "source": "sensor-a",
        "event_type": "temperature",
        "value": 20.0,
        "unit": "celsius",
        "metadata_json": {},
        "occurred_at": "2026-08-17T10:00:00Z",
    }

    client.post(
        "/api/v1/events",
        json=event,
        headers={
            "Idempotency-Key": "duplicate-cache-seed-1",
        },
    )

    with patch(
        "src.api.routes_events.invalidate_analytics_cache"
    ) as mock_invalidate:
        response = client.post(
            "/api/v1/events/batch",
            json={
                "events": [event]
            },
        )

    assert response.status_code == 200
    assert response.json()["accepted"] == 0
    assert response.json()["duplicates"] == 1
    mock_invalidate.assert_not_called()

def test_login_within_rate_limit(
    client,
):
    credentials = {
        "email": "rate-ok@example.com",
        "password": "StrongPassword123!",
    }

    client.post(
        "/api/v1/auth/register",
        json=credentials,
    )

    with patch(
        "src.core.rate_limit.redis_client.incr",
        return_value=1,
    ):
        response = client.post(
            "/api/v1/auth/login",
            json=credentials,
        )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_rate_limit_exceeded(
    client,
):
    credentials = {
        "email": "rate-limited@example.com",
        "password": "StrongPassword123!",
    }

    client.post(
        "/api/v1/auth/register",
        json=credentials,
    )

    with patch(
        "src.core.rate_limit.redis_client.incr",
        return_value=11,
    ):
        response = client.post(
            "/api/v1/auth/login",
            json=credentials,
        )

    assert response.status_code == 429

    body = response.json()

    assert body["error"]["message"] == "Rate limit exceeded"

    assert response.headers[
        "Retry-After"
    ] == "60"

def test_event_idempotency_stores_response(
    client,
):
    payload = {
        "event_id": "idempotent-event-1",
        "source": "sensor-a",
        "event_type": "temperature",
        "value": 25.0,
        "unit": "celsius",
        "metadata_json": {},
        "occurred_at": "2026-08-17T10:00:00Z",
    }

    with (
        patch(
            "src.core.idempotency.redis_client.get",
            return_value=None,
        ) as mock_get,
        patch(
            "src.core.idempotency.redis_client.setex",
            return_value=True,
        ) as mock_setex,
    ):
        response = client.post(
            "/api/v1/events",
            json=payload,
            headers={
                "Idempotency-Key": "idem-key-1",
            },
        )

    assert response.status_code == 201

    mock_get.assert_called_once_with(
        "idempotency:idem-key-1"
    )

    mock_setex.assert_called_once()


def test_event_idempotency_replays_cached_response(
    client,
):
    cached_response = {
        "event_id": "idempotent-event-2",
        "source": "sensor-a",
        "event_type": "temperature",
        "value": 30.0,
        "unit": "celsius",
        "metadata_json": {},
        "occurred_at": "2026-08-17T10:00:00Z",
        "ingested_at": "2026-08-17T10:00:01Z",
        "processed_at": "2026-08-17T10:00:02Z",
        "processing_status": "processed",
        "quality_status": "good",
        "normalized_value": 30.0,
    }

    with (
        patch(
            "src.core.idempotency.redis_client.get",
            return_value=json.dumps(
                cached_response
            ),
        ) as mock_get,
        patch(
            "src.core.idempotency.redis_client.setex",
        ) as mock_setex,
        patch(
            "src.api.routes_events.EventRepository.create",
        ) as mock_create,
    ):
        response = client.post(
            "/api/v1/events",
            json={
                "event_id": "different-request-body-id",
                "source": "sensor-b",
                "event_type": "vibration",
                "value": 99.0,
                "unit": "mm/s",
                "metadata_json": {},
                "occurred_at": "2026-08-17T11:00:00Z",
            },
            headers={
                "Idempotency-Key": "idem-key-2",
            },
        )

    assert response.status_code == 201

    assert (
        response.json()["event_id"]
        == "idempotent-event-2"
    )

    mock_get.assert_called_once_with(
        "idempotency:idem-key-2"
    )

    mock_create.assert_not_called()
    mock_setex.assert_not_called()