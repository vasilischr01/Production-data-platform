from prometheus_client import Counter, Histogram

EVENTS_INGESTED = Counter(
    "data_platform_events_ingested_total",
    "Total number of successfully ingested events",
)

EVENTS_DUPLICATE = Counter(
    "data_platform_events_duplicate_total",
    "Total number of duplicate events rejected",
)

EVENTS_PROCESSED = Counter(
    "data_platform_events_processed_total",
    "Total number of events processed",
    ["quality_status"],
)

INGEST_LATENCY = Histogram(
    "data_platform_event_ingest_duration_seconds",
    "Time spent ingesting a single event",
)