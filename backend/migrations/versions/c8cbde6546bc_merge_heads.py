"""merge heads

Revision ID: c8cbde6546bc
Revises: 0c9f0d1b7a2e, 3e8ee1489c4a
Create Date: 2026-04-15 09:24:09.368485

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c8cbde6546bc'
down_revision: Union[str, None] = ('0c9f0d1b7a2e', '3e8ee1489c4a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
