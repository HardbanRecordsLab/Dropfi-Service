"""HRL Digital sales agent — scoring/offer/pipeline columns on external_listings.

Idempotent: a FRESH database running 0001_baseline already creates these
columns (0001 reads the current SQLAlchemy models via create_all), so this
migration checks with the inspector before adding each one. Only a database
that ran 0001 before these columns existed needs this migration to actually
do anything.

Revision ID: 0002_radar_sales_agent
Revises: 0001_baseline
Create Date: 2026-10-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_radar_sales_agent"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "external_listings"

NEW_COLUMNS: list[sa.Column] = [
    sa.Column("fit_score", sa.Float(), nullable=True),
    sa.Column("fit_reason", sa.Text(), nullable=True),
    sa.Column("offer_text", sa.Text(), nullable=True),
    sa.Column("offer_language", sa.String(10), nullable=True),
    sa.Column("offer_price_min", sa.Float(), nullable=True),
    sa.Column("offer_price_max", sa.Float(), nullable=True),
    sa.Column("offer_questions", sa.JSON(), nullable=True),
    sa.Column("offer_generated_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("alerted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("pipeline", sa.String(20), nullable=True),
    sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("won_amount_pln", sa.Float(), nullable=True),
    sa.Column("pipeline_note", sa.Text(), nullable=True),
]

NEW_INDEXES = [
    ("ix_external_listings_fit_score", "fit_score"),
    ("ix_external_listings_pipeline", "pipeline"),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {c["name"] for c in inspector.get_columns(TABLE)}
    existing_indexes = {i["name"] for i in inspector.get_indexes(TABLE)}

    for column in NEW_COLUMNS:
        if column.name not in existing_columns:
            op.add_column(TABLE, column.copy())

    for index_name, column_name in NEW_INDEXES:
        if index_name not in existing_indexes:
            op.create_index(index_name, TABLE, [column_name])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_indexes = {i["name"] for i in inspector.get_indexes(TABLE)}
    existing_columns = {c["name"] for c in inspector.get_columns(TABLE)}

    for index_name, _ in NEW_INDEXES:
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=TABLE)

    for column in NEW_COLUMNS:
        if column.name in existing_columns:
            op.drop_column(TABLE, column.name)
