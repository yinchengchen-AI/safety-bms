"""add_signed_to_contract_status_enum

Revision ID: 91750585a912
Revises: 92ba9facf745
Create Date: 2026-04-14 02:19:32.083167

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "91750585a912"
down_revision: Union[str, None] = "92ba9facf745"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE contract_status ADD VALUE 'SIGNED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # A downgrade would require recreating the enum type.
    pass
