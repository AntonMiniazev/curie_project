"""seed public user roles

Revision ID: 20260613_161215
Revises: 20260611_110900
Create Date: 2026-06-13 16:12:15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260613_161215"
down_revision: str | None = "20260611_110900"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PUBLIC_USER_ROLES = (
    (
        "11111111-1111-4111-8111-111111111111",
        "region_directory",
        "Region directory: can see all regional data.",
    ),
    (
        "22222222-2222-4222-8222-222222222222",
        "store_fontaine",
        "Store - Fontaine: can see Fontaine store data.",
    ),
    (
        "33333333-3333-4333-8333-333333333333",
        "store_honeybee",
        "Store - Honeybee: can see Honeybee store data.",
    ),
    (
        "44444444-4444-4444-8444-444444444444",
        "store_tomcats",
        "Store - Tomcats: can see Tomcats store data.",
    ),
    (
        "55555555-5555-4555-8555-555555555555",
        "store_rosemary",
        "Store - Rosemary: can see Rosemary store data.",
    ),
    (
        "66666666-6666-4666-8666-666666666666",
        "store_suburban",
        "Store - Suburban: can see Suburban store data.",
    ),
)


def upgrade() -> None:
    for role_id, name, description in PUBLIC_USER_ROLES:
        op.execute(
            f"""
            INSERT INTO curie.roles (id, name, description)
            VALUES ('{role_id}', '{name}', '{description}')
            ON CONFLICT (name) DO UPDATE
            SET description = EXCLUDED.description
            """
        )


def downgrade() -> None:
    role_names = "', '".join(role[1] for role in PUBLIC_USER_ROLES)
    op.execute(
        f"""
        DELETE FROM curie.roles
        WHERE name IN ('{role_names}')
        """
    )
