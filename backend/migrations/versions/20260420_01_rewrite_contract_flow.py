"""rewrite contract flow

Revision ID: 20260420_01
Revises: f0f4758b66d4
Create Date: 2026-04-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260420_01"
down_revision: Union[str, None] = "f0f4758b66d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE contract_status RENAME TO contract_status_old")
    op.execute(
        "CREATE TYPE contract_status AS ENUM ('DRAFT', 'SIGNED', 'EXECUTING', 'COMPLETED', 'TERMINATED')"
    )
    op.execute(
        """
        ALTER TABLE contracts
        ALTER COLUMN status TYPE contract_status
        USING (
            CASE
                WHEN status::text = 'REVIEW' THEN 'DRAFT'
                WHEN status::text = 'ACTIVE' AND final_pdf_url IS NOT NULL THEN 'SIGNED'
                WHEN status::text = 'ACTIVE' THEN 'DRAFT'
                ELSE status::text
            END
        )::contract_status
        """
    )
    op.execute("DROP TYPE contract_status_old")

    op.create_table(
        "contract_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="附件文件名"),
        sa.Column("file_url", sa.String(length=500), nullable=False, comment="附件文件路径"),
        sa.Column(
            "file_type", sa.String(length=20), nullable=False, comment="draft / signed / other"
        ),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_contract_attachments_id"), "contract_attachments", ["id"], unique=False
    )

    op.execute(
        """
        INSERT INTO contract_attachments (
            contract_id,
            file_name,
            file_url,
            file_type,
            remark,
            uploaded_by,
            uploaded_at
        )
        SELECT
            id,
            COALESCE(
                NULLIF(regexp_replace(draft_doc_url, '^.*/', ''), ''),
                CONCAT('contract-', id, '-draft.docx')
            ),
            draft_doc_url,
            'draft',
            NULL,
            created_by,
            created_at
        FROM contracts
        WHERE draft_doc_url IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO contract_attachments (
            contract_id,
            file_name,
            file_url,
            file_type,
            remark,
            uploaded_by,
            uploaded_at
        )
        SELECT
            id,
            COALESCE(
                NULLIF(regexp_replace(standard_doc_url, '^.*/', ''), ''),
                CONCAT('contract-', id, '-draft.docx')
            ),
            standard_doc_url,
            'draft',
            NULL,
            created_by,
            created_at
        FROM contracts
        WHERE standard_doc_url IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO contract_attachments (
            contract_id,
            file_name,
            file_url,
            file_type,
            remark,
            uploaded_by,
            uploaded_at
        )
        SELECT
            id,
            COALESCE(
                NULLIF(regexp_replace(final_pdf_url, '^.*/', ''), ''),
                CONCAT('contract-', id, '-signed.pdf')
            ),
            final_pdf_url,
            'signed',
            NULL,
            created_by,
            created_at
        FROM contracts
        WHERE final_pdf_url IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_contract_attachments_id"), table_name="contract_attachments")
    op.drop_table("contract_attachments")

    op.execute("ALTER TYPE contract_status RENAME TO contract_status_new")
    op.execute(
        "CREATE TYPE contract_status AS ENUM ('DRAFT', 'REVIEW', 'ACTIVE', 'SIGNED', 'COMPLETED', 'TERMINATED')"
    )
    op.execute(
        """
        ALTER TABLE contracts
        ALTER COLUMN status TYPE contract_status
        USING (
            CASE
                WHEN status::text = 'SIGNED' THEN 'ACTIVE'
                WHEN status::text = 'EXECUTING' THEN 'SIGNED'
                ELSE status::text
            END
        )::contract_status
        """
    )
    op.execute("DROP TYPE contract_status_new")
