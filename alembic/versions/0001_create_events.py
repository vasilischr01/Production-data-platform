import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(64)),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("processing_status", sa.String(32), nullable=False),
        sa.Column("quality_status", sa.String(32), nullable=False),
        sa.Column("normalized_value", sa.Float()),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_events_source", "events", ["source"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"])

def downgrade():
    op.drop_table("events")
