"""add_service_types_table

Revision ID: 66bbcd563a10
Revises: 4bf2f7507f1d
Create Date: 2026-04-15 11:36:46.684276

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "66bbcd563a10"
down_revision: Union[str, None] = "4bf2f7507f1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 创建 service_types 表
    op.create_table(
        "service_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False, comment="机器标识"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="展示名称"),
        sa.Column(
            "default_price", sa.Numeric(precision=18, scale=2), nullable=True, comment="默认单价"
        ),
        sa.Column("standard_duration_days", sa.Integer(), nullable=True, comment="标准工期(天)"),
        sa.Column("qualification_requirements", sa.Text(), nullable=True, comment="资质要求"),
        sa.Column(
            "default_contract_template_id", sa.Integer(), nullable=True, comment="默认合同模板"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否启用"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["default_contract_template_id"], ["contract_templates.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_service_types_id"), "service_types", ["id"], unique=False)

    # 2. 插入初始数据
    service_types_table = sa.table(
        "service_types",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        service_types_table,
        [
            {
                "id": 1,
                "code": "evaluation",
                "name": "安全评价",
                "is_active": True,
                "created_at": "2026-01-01 00:00:00+00",
                "updated_at": "2026-01-01 00:00:00+00",
            },
            {
                "id": 2,
                "code": "training",
                "name": "安全培训",
                "is_active": True,
                "created_at": "2026-01-01 00:00:00+00",
                "updated_at": "2026-01-01 00:00:00+00",
            },
            {
                "id": 3,
                "code": "inspection",
                "name": "安全检测检验",
                "is_active": True,
                "created_at": "2026-01-01 00:00:00+00",
                "updated_at": "2026-01-01 00:00:00+00",
            },
            {
                "id": 4,
                "code": "consulting",
                "name": "安全咨询顾问",
                "is_active": True,
                "created_at": "2026-01-01 00:00:00+00",
                "updated_at": "2026-01-01 00:00:00+00",
            },
            {
                "id": 5,
                "code": "emergency_plan",
                "name": "应急预案编制",
                "is_active": True,
                "created_at": "2026-01-01 00:00:00+00",
                "updated_at": "2026-01-01 00:00:00+00",
            },
        ],
    )
    # 重置序列
    op.execute("SELECT setval('service_types_id_seq', 5, true)")

    # 3. contracts 表：添加临时列、更新数据、删除旧列、重命名
    op.add_column("contracts", sa.Column("service_type_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE contracts
        SET service_type_id = CASE service_type::text
            WHEN 'EVALUATION' THEN 1
            WHEN 'TRAINING' THEN 2
            WHEN 'INSPECTION' THEN 3
            WHEN 'CONSULTING' THEN 4
            WHEN 'EMERGENCY_PLAN' THEN 5
        END
    """
    )
    op.alter_column("contracts", "service_type_id", nullable=False)
    op.drop_column("contracts", "service_type")
    op.alter_column("contracts", "service_type_id", new_column_name="service_type")
    op.create_foreign_key(
        None, "contracts", "service_types", ["service_type"], ["id"], ondelete="RESTRICT"
    )

    # 4. service_orders 表
    op.add_column("service_orders", sa.Column("service_type_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE service_orders
        SET service_type_id = CASE service_type::text
            WHEN 'EVALUATION' THEN 1
            WHEN 'TRAINING' THEN 2
            WHEN 'INSPECTION' THEN 3
            WHEN 'CONSULTING' THEN 4
            WHEN 'EMERGENCY_PLAN' THEN 5
        END
    """
    )
    op.alter_column("service_orders", "service_type_id", nullable=False)
    op.drop_column("service_orders", "service_type")
    op.alter_column("service_orders", "service_type_id", new_column_name="service_type")
    op.create_foreign_key(
        None, "service_orders", "service_types", ["service_type"], ["id"], ondelete="RESTRICT"
    )

    # 5. contract_templates 表
    op.add_column("contract_templates", sa.Column("service_type_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE contract_templates
        SET service_type_id = CASE service_type::text
            WHEN 'EVALUATION' THEN 1
            WHEN 'TRAINING' THEN 2
            WHEN 'INSPECTION' THEN 3
            WHEN 'CONSULTING' THEN 4
            WHEN 'EMERGENCY_PLAN' THEN 5
        END
    """
    )
    op.alter_column("contract_templates", "service_type_id", nullable=False)
    op.drop_column("contract_templates", "service_type")
    op.alter_column("contract_templates", "service_type_id", new_column_name="service_type")
    op.create_foreign_key(
        None, "contract_templates", "service_types", ["service_type"], ["id"], ondelete="RESTRICT"
    )

    # 6. 删除旧 ENUM 类型
    op.execute("DROP TYPE IF EXISTS service_type")
    op.execute("DROP TYPE IF EXISTS service_type_order")


def downgrade() -> None:
    pass
