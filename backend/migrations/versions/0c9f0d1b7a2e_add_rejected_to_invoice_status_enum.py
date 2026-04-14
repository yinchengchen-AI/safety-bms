"""add_rejected_to_invoice_status_enum

Revision ID: 0c9f0d1b7a2e
Revises: 91750585a912
Create Date: 2026-04-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0c9f0d1b7a2e"
down_revision: Union[str, None] = "91750585a912"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'invoice_status'
          AND e.enumlabel = 'REJECTED'
    ) THEN
        ALTER TYPE invoice_status ADD VALUE 'REJECTED';
    END IF;
END $$;
"""
    )


def downgrade() -> None:
    pass
