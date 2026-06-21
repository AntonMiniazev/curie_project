"""seed marketing report

Revision ID: 20260621_180000
Revises: 20260613_161215
Create Date: 2026-06-21 18:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260621_180000"
down_revision: str | None = "20260613_161215"
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
        VALUES (
            'orders-sales',
            'Marketing Reporting',
            'Marketing sales and client behavior dashboard backed by the Curie local cache.',
            'Marketing',
            '/',
            'region_directory',
            true,
            10
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
        WHERE id = 'orders-sales'
        """
    )
