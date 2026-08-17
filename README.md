# Production Data Platform

A production-style backend and data engineering platform built with **FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy, Alembic, Docker Compose, Prometheus, JWT authentication, role-based access control, structured logging, automated tests, and GitHub Actions**.

The project demonstrates how a modern service can ingest, validate, persist, process, secure, monitor, cache, and expose event data through a versioned REST API.

> This is a portfolio / engineering project intended to demonstrate production-oriented backend and data-platform patterns.

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
                         │ REST + Validation    │
                         │ Auth + RBAC          │
                         │ Rate Limiting        │
                         │ Idempotency          │
                         └───────┬───────┬──────┘
                                 │       │
                    ┌────────────┘       └────────────┐
                    ▼                                 ▼
          ┌──────────────────┐              ┌──────────────────┐
          │    PostgreSQL    │              │      Redis       │
          │ Events + Users   │              │ Broker + Cache   │
          └────────┬─────────┘              │ Rate Limit State │
                   │                        │ Idempotency Store │
                   │                        └────────┬─────────┘
                   │                                 │
                   │                                 ▼
                   │                       ┌──────────────────┐
                   │                       │  Celery Worker   │
                   │                       │ Event Processing │
                   │                       └────────┬─────────┘
                   │                                │
                   └────────────────┬───────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Analytics API      │
                         │ Redis TTL Cache      │
                         │ Prometheus Metrics   │
                         │ Structured Logs      │
                         └──────────────────────┘
```

Events are accepted by FastAPI, persisted in PostgreSQL, optionally queued through Redis for Celery processing, enriched by the processing pipeline, and exposed through event and analytics APIs. Redis is also used for analytics caching, authentication rate limiting, and idempotency state.

---

## Key Features

### API and data ingestion

- Versioned REST API built with FastAPI
- Single-event ingestion
- Batch ingestion
- Pydantic request/response validation
- Duplicate-event protection using unique `event_id`
- Event filtering and pagination
- Explicit processing endpoint
- Aggregated analytics endpoints

### Persistence and processing

- PostgreSQL persistence
- SQLAlchemy 2.x ORM
- Alembic database migrations
- Repository layer for database access
- Service layer for processing and quality rules
- Redis message broker
- Celery asynchronous background processing
- Event quality checks
- Value normalization

### Authentication and authorization

- User registration and login
- JWT bearer authentication
- Password hashing
- Current-user endpoint
- Typed user roles
- Role-based access control (RBAC)
- Admin-only user-management endpoints
- Pagination, filtering, email search, and sorting for admin user queries

### Reliability and API protection

- Redis-backed rate limiting for authentication endpoints
- `429 Too Many Requests` responses with `Retry-After`
- Redis-backed idempotency for single-event ingestion
- `Idempotency-Key` support for safe request replay
- Analytics cache invalidation after event writes
- Duplicate-only batches avoid unnecessary cache invalidation

### Caching

- Redis TTL cache for analytics summary
- Cache-hit and cache-miss paths
- Automatic invalidation after relevant event mutations
- Configurable analytics cache TTL

### Observability

- `/health` liveness endpoint
- `/ready` readiness endpoint
- Readiness checks for database and Redis
- Prometheus-compatible metrics
- Custom ingestion, duplicate, processing, and latency metrics
- Structured JSON logging
- Request IDs propagated through responses
- Request tracing middleware
- Centralized error responses
- HTTP exception headers preserved by the global error handler

### Engineering quality

- Docker and Docker Compose
- Environment-variable configuration
- pytest automated test suite
- Integration-style API tests
- Redis/Celery behavior mocked where appropriate for deterministic tests
- Ruff linting
- GitHub Actions CI
- Secrets, local databases, caches, and virtual environments excluded from version control

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

### Distributed / Async Infrastructure

- Redis
- Celery

### Security

- JWT authentication
- Password hashing
- RBAC
- Redis-backed rate limiting
- Idempotency keys

### Observability

- Prometheus Client
- Structured JSON logging
- Request tracing / request IDs
- Centralized exception handling

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
│   │   ├── 0001_create_events.py
│   │   └── ..._add_users_table.py
│   ├── env.py
│   └── script.py.mako
│
├── src/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── errors.py
│   │   ├── main.py
│   │   ├── middleware.py
│   │   ├── routes_admin.py
│   │   ├── routes_analytics.py
│   │   ├── routes_auth.py
│   │   ├── routes_events.py
│   │   └── routes_users.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── idempotency.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── rate_limit.py
│   │   ├── redis.py
│   │   ├── request_context.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── event.py
│   │   └── user.py
│   │
│   ├── repositories/
│   │   ├── events.py
│   │   └── users.py
│   │
│   ├── schemas/
│   │   ├── analytics.py
│   │   ├── event.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── cache.py
│   │   ├── processing.py
│   │   └── quality.py
│   │
│   └── workers/
│       ├── celery_app.py
│       └── tasks.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_security.py
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

## Event Data Model

Example event payload:

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
        │
        ▼
Validate request
        │
        ▼
Validate Idempotency-Key
        │
        ├──────── cache hit ────────► replay stored response
        │
        ▼
Check duplicate event_id
        │
        ▼
Persist event in PostgreSQL
        │
        ▼
processing_status = pending
        │
        ▼
Queue Celery task through Redis
        │
        ▼
Celery worker processes event
        │
        ▼
Quality assessment
        │
        ▼
Value normalization
        │
        ▼
processing_status = processed
        │
        ▼
Invalidate analytics cache
        │
        ▼
Store idempotent response
```

When `PROCESS_ASYNC=false`, processing runs synchronously, which is useful for local development and deterministic tests.

---

## API Endpoints

### System

```text
GET /health
GET /ready
GET /metrics
```

### Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

### Users

```text
GET /api/v1/users/me
```

### Admin

```text
GET /api/v1/admin/users
```

The admin user endpoint supports pagination and query capabilities including role filtering, email search, and sorting.

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

Interactive API documentation is available through Swagger UI at `/docs`.

---

## Authentication and RBAC

Users can register and authenticate through the API. Successful login returns a bearer access token.

Protected endpoints use JWT validation through FastAPI dependencies.

Two user roles are currently represented:

```text
user
admin
```

Regular users can access their own authenticated profile, while admin-only routes require the `admin` role.

The admin user listing supports:

- pagination
- role filtering
- email search
- sorting
- typed role validation

This keeps authorization logic at the API dependency layer instead of duplicating role checks throughout route handlers.

---

## Rate Limiting

Authentication endpoints are protected with a Redis-backed fixed-window rate limiter.

The limiter tracks requests by scope and client address using Redis counters.

Configuration:

```text
AUTH_RATE_LIMIT_REQUESTS=10
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
```

When the limit is exceeded, the API returns:

```text
429 Too Many Requests
```

with a `Retry-After` response header.

The centralized HTTP exception handler preserves exception headers, ensuring protocol-level metadata such as `Retry-After` is not lost.

---

## Idempotent Event Ingestion

Single-event ingestion supports an `Idempotency-Key` request header.

Example:

```http
POST /api/v1/events
Idempotency-Key: event-request-123
Content-Type: application/json
```

On the first request:

1. Redis is checked for the idempotency key.
2. The event is created and processed.
3. The serialized response is stored in Redis with a TTL.

On a repeated request using the same key:

1. the cached response is returned;
2. event creation is skipped;
3. no duplicate write is performed.

This models a common production pattern for clients that may retry requests after network failures or timeouts.

---

## Analytics and Redis Caching

The analytics summary endpoint exposes aggregate operational statistics:

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

The summary is cached in Redis using a TTL.

Request flow:

```text
GET /api/v1/analytics/summary
            │
            ▼
       Redis lookup
        ┌───┴───┐
      hit      miss
       │         │
       ▼         ▼
   response   PostgreSQL
                 │
                 ▼
             aggregate
                 │
                 ▼
            Redis SETEX
                 │
                 ▼
              response
```

The cache is invalidated after event writes that can change analytics results.

A batch containing only duplicate events does not invalidate the cache unnecessarily.

Additional grouping endpoints:

```text
GET /api/v1/analytics/by-source
GET /api/v1/analytics/by-type
```

---

## Observability

### Prometheus metrics

Metrics are exposed at:

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

These provide visibility into:

- successful event ingestion
- duplicate rejection
- processed events grouped by quality status
- ingestion latency

### Request tracing

Each request is associated with a request ID.

Clients can supply an `X-Request-ID`, or the application generates one when absent.

The response includes the request ID so client-side failures can be correlated with server logs.

### Structured logging

Application and request lifecycle events are emitted as structured JSON.

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

Request start/completion logs also include request context such as method, path, response status, request ID, and duration.

### Centralized error handling

The API uses centralized handlers for:

- `HTTPException`
- request validation errors
- unexpected exceptions

Errors follow a consistent response structure and include the request ID for traceability.

---

## Health and Readiness

Liveness:

```text
GET /health
```

Readiness:

```text
GET /ready
```

The readiness endpoint checks application dependencies including:

- database connectivity
- Redis connectivity

This separates "the process is alive" from "the service is ready to handle traffic."

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

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Run database migrations:

```bash
alembic upgrade head
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

Build and start the stack:

```bash
docker compose up --build
```

Services include:

```text
api      - FastAPI application
db       - PostgreSQL
redis    - Redis broker/cache/state store
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

Alembic manages version-controlled database schema changes.

Apply all migrations:

```bash
alembic upgrade head
```

The migration history includes the event schema and user-management schema.

---

## Configuration

Configuration is loaded from environment variables through the application settings layer.

Representative values:

```env
APP_NAME=Production Data Platform
APP_ENV=development
LOG_LEVEL=INFO

DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/dataplatform
REDIS_URL=redis://redis:6379/0

PROCESS_ASYNC=true

ANALYTICS_CACHE_TTL_SECONDS=60

AUTH_RATE_LIMIT_REQUESTS=10
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
```

Use `.env.example` as the source template.

Real `.env` files are excluded from version control.

---

## Testing

Run:

```bash
pytest -q
```

Current development result:

```text
33 passed
```

The suite covers:

- health checks
- dependency readiness
- event ingestion
- duplicate rejection
- event retrieval
- batch ingestion
- filtering
- synchronous and asynchronous processing behavior
- analytics aggregation
- analytics cache misses
- analytics cache hits
- analytics cache invalidation
- user registration
- duplicate registration
- login
- invalid credentials
- JWT access
- current-user access
- RBAC
- admin pagination
- admin filtering
- admin email search
- admin sorting
- request ID generation
- request ID preservation
- authentication rate limiting
- `Retry-After` behavior
- idempotency response storage
- idempotent response replay

Test fixtures isolate the SQLite test database between tests and mock Redis interactions where external infrastructure is not the behavior under test.

---

## Linting

Run Ruff:

```bash
ruff check .
```

Apply supported automatic fixes:

```bash
ruff check . --fix
```

The project is maintained with a clean Ruff check before commits.

---

## Continuous Integration

GitHub Actions runs automatically on pushes and pull requests to `main`.

The CI quality gate performs:

```text
Install dependencies
        │
        ▼
Run Ruff
        │
        ▼
Run pytest
```

This prevents linting or test regressions from being merged unnoticed.

---

## Data Quality

The processing service performs basic event-quality checks independently from the HTTP layer.

Current statuses include:

```text
good
bad
unknown
```

Keeping quality logic inside the service layer makes it straightforward to extend with:

- physical sensor-range validation
- missing-value detection
- outlier detection
- schema-version validation
- timestamp-consistency checks
- source-specific validation rules

---

## Design Decisions

### PostgreSQL

Provides durable relational persistence for events and users while supporting constraints, indexing, transactions, and analytical queries.

### Redis

Redis serves several infrastructure roles:

- Celery message broker
- analytics cache
- rate-limit state
- idempotency state
- readiness dependency

Using a single infrastructure component for these concerns keeps the local stack compact while still demonstrating distributed-service patterns.

### Celery

Moves potentially expensive processing work out of the HTTP request path when asynchronous processing is enabled.

### Repository Layer

Keeps database access isolated from route handlers.

### Service Layer

Separates processing, quality, and cache behavior from persistence and HTTP transport concerns.

### JWT and RBAC

JWT provides stateless API authentication, while typed roles and reusable dependencies centralize authorization rules.

### Idempotency Keys

Protect write operations from accidental duplicate execution during client retries.

### Redis Rate Limiting

Demonstrates API abuse protection using shared distributed state rather than in-process counters.

### Cache Invalidation

The analytics cache is invalidated by relevant write operations instead of relying only on TTL expiration.

### Alembic

Provides explicit, version-controlled database migrations.

### Prometheus Metrics

Exposes operational counters and latency measurements in a standard monitoring format.

### Structured Logging and Request IDs

Machine-readable logs and request correlation make production debugging substantially easier than unstructured console output.

### Docker Compose

Makes the multi-service environment reproducible locally.

---

## Production-Oriented Characteristics

This repository goes beyond a basic CRUD API.

It demonstrates:

- relational persistence
- schema migrations
- asynchronous task execution
- service and repository layering
- JWT authentication
- role-based authorization
- secure password handling
- rate limiting
- idempotent writes
- Redis caching
- explicit cache invalidation
- health/readiness separation
- request tracing
- structured logging
- centralized error handling
- Prometheus metrics
- deterministic automated tests
- CI automation
- multi-service containerization
- environment-based configuration

The project is relevant to **backend engineering, software engineering, data engineering, ML infrastructure, and applied AI platform engineering** roles.

---

## Security

Sensitive configuration belongs in environment variables.

The repository excludes local artifacts such as:

```text
.env
local SQLite databases
virtual environments
cache files
```

Security-oriented features implemented in the application include:

- password hashing
- JWT authentication
- RBAC
- authentication rate limiting
- standardized error handling
- no secrets embedded in source code

No credentials or secrets should be committed to Git.

---

## Future Improvements

Potential next steps, intentionally left outside the current scope:

- refresh-token rotation
- account lockout / suspicious-login detection
- audit logging for privileged operations
- OpenTelemetry distributed tracing
- Grafana dashboards
- dead-letter queues
- retry policies with exponential backoff
- Kafka streaming ingestion
- Schema Registry
- Kubernetes deployment
- cloud deployment
- PostgreSQL table partitioning
- data warehouse integration
- dbt transformations
- load testing with Locust
- horizontal Celery worker scaling

The current scope is intentionally focused on a complete, testable production-style backend rather than adding infrastructure only for breadth.

---

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.
