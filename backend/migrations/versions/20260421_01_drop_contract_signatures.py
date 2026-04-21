"""drop contract_signatures table and contract:sign permission

Revision ID: 20260421_01
Revises: 20260420_01
Create Date: 2026-04-21 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260421_01"
down_revision: Union[str, None] = "20260420_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 删除 contract_signatures 表
    op.drop_table("contract_signatures")

    # 删除 permissions 表中 contract:sign 权限
    op.execute("DELETE FROM permissions WHERE code = 'contract:sign'")

    # 删除角色-权限关联中的 contract:sign（通过 permissions 外键级联已处理，
    # 若无外键级联则手动清理）
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions WHERE code = 'contract:sign'
        )
        """
    )


def downgrade() -> None:
    op.create_table(
        "contract_signatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column(
            "party", sa.String(length=20), nullable=False, comment="签署方: party_a / party_b"
        ),
        sa.Column("signed_by", sa.String(length=100), nullable=True, comment="签署人姓名"),
        sa.Column(
            "signature_url", sa.String(length=500), nullable=False, comment="签名图片 MinIO 路径"
        ),
        sa.Column(
            "signed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="签署时间",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["contracts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
