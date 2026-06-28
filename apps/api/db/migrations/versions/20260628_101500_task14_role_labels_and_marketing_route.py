"""task14 role labels and marketing route

Revision ID: 20260628_101500
Revises: 20260625_231500
Create Date: 2026-06-28 10:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_101500"
down_revision: str | None = "20260625_231500"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROLE_SHORT_DESCRIPTIONS = (
    ("region_directory", "Region Directory"),
    ("store_fontaine", "Fontaine store"),
    ("store_honeybee", "Honeybee store"),
    ("store_tomcats", "Tomcats store"),
    ("store_rosemary", "Rosemary store"),
    ("store_suburban", "Suburban store"),
)


def upgrade() -> None:
    op.add_column(
        "roles",
        sa.Column("short_description", sa.String(length=80), nullable=True),
        schema="curie",
    )

    for role_name, short_description in ROLE_SHORT_DESCRIPTIONS:
        op.execute(
            f"""
            UPDATE curie.roles
            SET short_description = '{short_description}'
            WHERE name = '{role_name}'
            """
        )

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
            'marketing-sales',
            'Marketing Reporting',
            'Marketing sales and client behavior dashboard backed by the Curie local cache.',
            'Marketing',
            '/?report=marketing',
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
    op.execute(
        """
        DELETE FROM curie.reports
        WHERE id = 'orders-sales'
        """
    )


def downgrade() -> None:
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
    op.execute(
        """
        DELETE FROM curie.reports
        WHERE id = 'marketing-sales'
        """
    )
    op.drop_column("roles", "short_description", schema="curie")
