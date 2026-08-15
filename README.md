# Production Data Platform

A production-style backend and data engineering platform built with FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy, Alembic, Docker Compose, Prometheus, structured logging, automated tests, and GitHub Actions.

The project demonstrates how a modern data platform can ingest, validate, persist, process, monitor, and expose event data through a clean REST API.

---

## Architecture

```text
                     ┌──────────────────────┐
                     │   Client / Producer  │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │       FastAPI        │
                     │  Validation / REST   │
                     └───────┬───────┬──────┘
                             │       │
                             │       │
                             ▼       ▼
                 ┌──────────────┐   ┌──────────────┐
                 │ PostgreSQL   │   │    Redis     │
                 │ Event Store  │   │ Task Broker  │
                 └──────┬───────┘   └──────┬───────┘
                        │                  │
                        │                  ▼
                        │          ┌──────────────┐
                        │          │ Celery Worker│
                        │          │ Processing   │
                        │          └──────┬───────┘
                        │                 │
                        └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Analytics API   │
                         │ + Prometheus    │
                         └─────────────────┘
```

Events are accepted by the API, persisted in PostgreSQL, queued through Redis, processed asynchronously by Celery, and written back to PostgreSQL.

---

## Features

- REST API built with FastAPI
- Single-event ingestion
- Batch ingestion
- Pydantic schema validation
- Duplicate-event protection using unique `event_id`
- PostgreSQL persistence
- SQLAlchemy 2.x ORM
- Alembic database migrations
- Redis message broker
- Celery asynchronous background processing
- Event quality checks
- Value normalization
- Filtering and pagination
- Aggregated analytics endpoints
- Health and readiness probes
- Prometheus-compatible monitoring
- Custom ingestion, duplicate, processing, and latency metrics
- Structured JSON logging
- Docker and Docker Compose
- Automated tests with pytest
- Async processing integration test
- Ruff linting
- GitHub Actions CI
- Environment-variable configuration
- Secrets and local databases excluded from version control

---

## Technology Stack

### Backend

- Python 3.11
- FastAPI
- Pydantic
- Uvicorn

### Data Layer

- PostgreSQL
- SQLAlchemy
- Alembic

### Async Processing

- Redis
- Celery

### Observability

- Prometheus Client
- Structured JSON logging

### Engineering

- Docker
- Docker Compose
- pytest
- Ruff
- GitHub Actions

---

## Project Structure

```text
production-data-platform/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── alembic/
│   ├── versions/
│   │   └── 0001_create_events.py
│   └── env.py
│
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes_events.py
│   │   └── routes_analytics.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── metrics.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   │   └── event.py
│   │
│   ├── repositories/
│   │   └── events.py
│   │
│   ├── schemas/
│   │   ├── event.py
│   │   └── analytics.py
│   │
│   ├── services/
│   │   ├── processing.py
│   │   └── quality.py
│   │
│   └── workers/
│       ├── celery_app.py
│       └── tasks.py
│
├── tests/
│   ├── conftest.py
│   └── test_api.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## Data Model

Each event contains:

```json
{
  "event_id": "evt-0001",
  "source": "machine-a",
  "event_type": "temperature",
  "value": 72.4,
  "unit": "celsius",
  "metadata": {
    "factory": "plant-1"
  },
  "occurred_at": "2026-08-14T09:00:00Z"
}
```

Stored events also contain processing metadata such as:

```text
ingested_at
processed_at
processing_status
quality_status
normalized_value
```

---

## Event Processing Flow

```text
POST /api/v1/events
        |
        ▼
Validate request
        |
        ▼
Check duplicate event_id
        |
        ▼
Persist event in PostgreSQL
        |
        ▼
processing_status = pending
        |
        ▼
Send Celery task through Redis
        |
        ▼
Celery worker processes event
        |
        ▼
Quality assessment
        |
        ▼
Value normalization
        |
        ▼
processing_status = processed
        |
        ▼
Updated record stored in PostgreSQL
```

---

## API Endpoints

### System

```text
GET /health
GET /ready
```

### Events

```text
POST /api/v1/events
POST /api/v1/events/batch
GET  /api/v1/events
GET  /api/v1/events/{event_id}
POST /api/v1/events/{event_id}/process
```

### Analytics

```text
GET /api/v1/analytics/summary
GET /api/v1/analytics/by-source
GET /api/v1/analytics/by-type
```

### Observability

```text
GET /metrics
```

---

## Example Event Ingestion

Request:

```json
{
  "event_id": "evt-0001",
  "source": "machine-a",
  "event_type": "temperature",
  "value": 72.4,
  "unit": "celsius",
  "metadata": {
    "factory": "plant-1"
  },
  "occurred_at": "2026-08-14T09:00:00Z"
}
```

Initial asynchronous state:

```json
{
  "event_id": "evt-0001",
  "processing_status": "pending",
  "quality_status": "unknown",
  "normalized_value": null
}
```

After background processing:

```json
{
  "event_id": "evt-0001",
  "processing_status": "processed",
  "quality_status": "good",
  "normalized_value": 0.9863760217983651
}
```

---

## Analytics

The platform exposes aggregated operational statistics.

Example endpoint:

```text
GET /api/v1/analytics/summary
```

Example response:

```json
{
  "total_events": 100,
  "processed_events": 98,
  "pending_events": 2,
  "good_quality_events": 95,
  "bad_quality_events": 3,
  "average_value": 42.7
}
```

Additional grouping endpoints:

```text
GET /api/v1/analytics/by-source
GET /api/v1/analytics/by-type
```

---

## Observability

Prometheus-compatible metrics are exposed at:

```text
GET /metrics
```

Custom metrics include:

```text
data_platform_events_ingested_total
data_platform_events_duplicate_total
data_platform_events_processed_total
data_platform_event_ingest_duration_seconds
```

These metrics provide visibility into:

- successful event ingestion
- duplicate rejections
- processed events grouped by quality status
- ingestion latency

Example:

```text
data_platform_events_ingested_total 1.0
data_platform_events_processed_total{quality_status="good"} 1.0
```

---

## Structured Logging

Application events are emitted as structured JSON logs.

Example:

```json
{
  "levelname": "INFO",
  "name": "src.api.routes_events",
  "message": "event_ingested",
  "event_id": "evt-log-001",
  "source": "machine-log",
  "event_type": "temperature"
}
```

Duplicate-event rejection is also logged.

---

## Local Development

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn src.api.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Docker Deployment

Build and start the full stack:

```bash
docker compose up --build
```

Services:

```text
api      - FastAPI application
db       - PostgreSQL
redis    - Redis message broker
worker   - Celery worker
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Stop the stack:

```bash
docker compose down
```

---

## Database Migrations

Alembic manages database schema migrations.

Apply migrations:

```bash
alembic upgrade head
```

The Docker API container also applies migrations during startup.

---

## Testing

Run the automated test suite:

```bash
pytest -q
```

The test suite covers:

- health endpoint
- readiness endpoint
- event ingestion
- duplicate-event rejection
- event retrieval
- batch ingestion
- event filtering
- analytics aggregation
- asynchronous processing behavior
- transition from `pending` to `processed`

Current development result:

```text
5 passed
```

---

## Async Processing Test

The automated test suite verifies asynchronous behavior without requiring a real Redis or Celery worker during pytest execution.

It verifies that:

1. an event starts with `processing_status = pending`
2. the correct Celery task is queued
3. processing logic runs
4. the event transitions to `processed`
5. quality status is assigned
6. a normalized value is generated

The complete Redis/Celery workflow has also been verified manually through Docker Compose.

---

## Linting

Run Ruff:

```bash
ruff check .
```

Automatically fix supported issues:

```bash
ruff check . --fix
```

The project currently passes Ruff checks.

---

## Continuous Integration

GitHub Actions runs automatically on pushes and pull requests to `main`.

The CI workflow performs:

```text
Install dependencies
        |
        ▼
Run Ruff
        |
        ▼
Run pytest
```

This provides an automated quality gate for repository changes.

---

## Configuration

Configuration is loaded from environment variables.

Example:

```text
APP_NAME=Production Data Platform
APP_ENV=development
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/dataplatform
REDIS_URL=redis://redis:6379/0
PROCESS_ASYNC=true
```

Use `.env.example` as a template.

Real `.env` files are excluded from version control.

---

## Data Quality

The processing service performs basic event-quality checks.

Possible statuses:

```text
good
bad
unknown
```

The quality logic is separated from the HTTP layer so it can be extended independently.

Potential extensions include:

- physical sensor-range validation
- missing-value detection
- outlier detection
- schema-version validation
- timestamp-consistency checks
- source-specific validation rules

---

## Design Decisions

### PostgreSQL

Provides persistent relational storage suitable for production-style backend systems.

### Redis and Celery

Separates background processing from HTTP request handling.

### Repository Layer

Keeps database access isolated from API routes.

### Service Layer

Separates processing and quality logic from persistence and transport concerns.

### Alembic

Provides explicit version-controlled database migrations.

### Prometheus Metrics

Makes application behavior observable with counters and latency histograms.

### Structured Logging

Produces machine-readable logs suitable for centralized logging systems.

### Docker Compose

Allows the complete multi-service environment to be reproduced locally.

---

## Production-Oriented Characteristics

This repository goes beyond a basic CRUD API.

It includes:

- asynchronous task processing
- relational persistence
- database migrations
- duplicate protection
- health and readiness checks
- observability
- structured logging
- integration-style tests
- CI automation
- multi-service containerization
- environment-based configuration

The project demonstrates engineering practices relevant to backend engineering, data engineering, ML infrastructure, and applied AI systems.

---

## Future Improvements

Potential extensions include:

- Apache Kafka streaming ingestion
- dead-letter queues
- retry policies with exponential backoff
- Schema Registry
- OpenTelemetry distributed tracing
- Grafana dashboards
- authentication and RBAC
- Kubernetes deployment
- cloud deployment
- PostgreSQL table partitioning
- audit logging
- data warehouse integration
- dbt transformations
- load testing with Locust
- rate limiting
- API versioning
- horizontal Celery worker scaling

---

## Security

Sensitive configuration should be stored only in environment variables.

The repository excludes:

```text
.env
local SQLite databases
virtual environments
cache files
```

No credentials or secrets should be committed to Git.

---

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.