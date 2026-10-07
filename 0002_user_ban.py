"""users.is_banned / users.ban_reason

Revision ID: 0002_user_ban
Revises: 0001_initial
Create Date: 2026-10-07
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_user_ban"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}


def upgrade() -> None:
    # 0001 создаёт схему из актуальной метадаты, поэтому на новой БД колонки уже есть.
    cols = _columns()
    if "is_banned" not in cols:
        op.add_column("users", sa.Column("is_banned", sa.Boolean(), nullable=False,
                                         server_default=sa.false()))
    if "ban_reason" not in cols:
        op.add_column("users", sa.Column("ban_reason", sa.String(255), nullable=True))


def downgrade() -> None:
    cols = _columns()
    if "ban_reason" in cols:
        op.drop_column("users", "ban_reason")
    if "is_banned" in cols:
        op.drop_column("users", "is_banned")
