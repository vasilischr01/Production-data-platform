from unittest.mock import patch

from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.db.session import engine
from src.models.user import User


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
    r = client.post("/api/v1/events", json=event())
    assert r.status_code == 201
    assert r.json()["processing_status"] == "processed"

    r = client.get("/api/v1/events/evt-1")
    assert r.status_code == 200

    r = client.post("/api/v1/events", json=event())
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
    client.post("/api/v1/events", json=event("1", "machine-a", "temperature", 10))
    client.post("/api/v1/events", json=event("2", "machine-a", "vibration", 20))
    client.post("/api/v1/events", json=event("3", "machine-b", "temperature", 30))

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

        response = client.post("/api/v1/events", json=payload)

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
            role="admin",
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

    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["email"] == "admin@example.com"
    assert body[0]["role"] == "admin"