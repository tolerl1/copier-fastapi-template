"""Create items table.

Revision ID: 0001
Revises: None
Create Date: 2026-07-11 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_EXAMPLE_ITEMS = [
    {"name": "Example Item 1", "description": "First example item"},
    {"name": "Example Item 2", "description": "Second example item"},
    {"name": "Example Item 3", "description": "Third example item"},
]


def upgrade() -> None:
    """Creates and seeds the example items table.

    Returns:
        None: Migration operations run in-place.
    """

    items_table = op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
    )
    op.bulk_insert(items_table, _EXAMPLE_ITEMS)


def downgrade() -> None:
    """Drops the items table.

    Returns:
        None: Migration operations run in-place.
    """

    op.drop_table("items")
