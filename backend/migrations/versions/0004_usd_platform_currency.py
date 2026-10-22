"""Platform currency is USD: external_listings.won_amount_pln -> won_amount_usd.

Revision ID: 0004_usd_platform_currency
Revises: 0003_messages
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_usd_platform_currency"
down_revision: Union[str, None] = "0003_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0001 runs create_all from the current models, so a fresh DB already has the new name.
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("external_listings")}
    if "won_amount_pln" in cols and "won_amount_usd" not in cols:
        op.alter_column("external_listings", "won_amount_pln", new_column_name="won_amount_usd")


def downgrade() -> None:
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("external_listings")}
    if "won_amount_usd" in cols and "won_amount_pln" not in cols:
        op.alter_column("external_listings", "won_amount_usd", new_column_name="won_amount_pln")
