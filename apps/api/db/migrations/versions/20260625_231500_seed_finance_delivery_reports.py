"""seed finance and delivery reports

Revision ID: 20260625_231500
Revises: 20260621_180000
Create Date: 2026-06-25 23:15:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260625_231500"
down_revision: str | None = "20260621_180000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO curie.reports (
            id,
            title,
            description,
            category,
            streamlit_path,
            required_role,
            enabled,
            sort_order
        )
        VALUES
          (
            'finance-performance',
            'Finance Performance',
            'Revenue, margin, operational profit, and product margin dashboard backed by the Curie local cache.',
            'Finance',
            '/?report=finance',
            'region_directory',
            true,
            20
          ),
          (
            'delivery-operations',
            'Delivery Operations',
            'Courier workload and tariff dashboard backed by the Curie local cache.',
            'Delivery',
            '/?report=delivery',
            'region_directory',
            true,
            30
          )
        ON CONFLICT (id) DO UPDATE
        SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            streamlit_path = EXCLUDED.streamlit_path,
            required_role = EXCLUDED.required_role,
            enabled = EXCLUDED.enabled,
            sort_order = EXCLUDED.sort_order,
            updated_at = now()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM curie.reports
        WHERE id IN ('finance-performance', 'delivery-operations')
        """
    )
