"""create rules table

Revision ID: 9e02a8e1603b
Revises:
Create Date: 2026-08-06 12:17:24.656699

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e02a8e1603b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the rules table."""

    op.create_table(
        "rules",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "mode",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "value",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.CheckConstraint(
            "type IN ('ip', 'domain', 'port')",
            name="ck_rules_type",
        ),
        sa.CheckConstraint(
            "mode IN ('blacklist', 'whitelist')",
            name="ck_rules_mode",
        ),
        sa.UniqueConstraint(
            "type",
            "mode",
            "value",
            name="uq_rules_type_mode_value",
        ),
    )


def downgrade() -> None:
    """Remove the rules table."""

    op.drop_table("rules")