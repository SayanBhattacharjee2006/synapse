"""add upload status to documents

Revision ID: a1b2c3d4e5f6
Revises: 66562afc14bd
Create Date: 2026-11-07 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "66562afc14bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

upload_status_enum = postgresql.ENUM(
    "pending", "completed", "failed", name="uploadstatusenum"
)


def upgrade() -> None:
    """Upgrade schema and backfill existing documents."""
    upload_status_enum.create(op.get_bind(), checkfirst=True)
    # 1. Add uploadStatus with server_default='completed' so existing documents receive 'completed'
    op.add_column(
        "documents",
        sa.Column(
            "uploadStatus",
            sa.Enum("pending", "completed", "failed", name="uploadstatusenum"),
            nullable=False,
            server_default="completed",
        ),
    )
    # 2. Add uploadConfirmedAt column
    op.add_column(
        "documents",
        sa.Column(
            "uploadConfirmedAt",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # 3. Backfill uploadConfirmedAt from createdAt for existing documents
    op.execute(
        'UPDATE documents SET "uploadConfirmedAt" = "createdAt" WHERE "uploadConfirmedAt" IS NULL'
    )
    # 4. Alter server_default to 'pending' for all new initiated uploads
    op.alter_column(
        "documents",
        "uploadStatus",
        server_default="pending",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("documents", "uploadConfirmedAt")
    op.drop_column("documents", "uploadStatus")
    upload_status_enum.drop(op.get_bind(), checkfirst=True)
