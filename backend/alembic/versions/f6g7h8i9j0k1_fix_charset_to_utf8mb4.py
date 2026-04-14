"""fix charset to utf8mb4 for master data tables

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-01-15 14:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = [
        'md_unit_dimension',
        'md_unit',
        'md_unit_conversion',
        'md_resource_category',
        'md_attr_definition',
        'md_material',
        'md_equipment',
        'md_process',
        'md_process_resource',
        'md_labor',
        'md_energy_rate',
        'md_energy_calendar',
    ]

    for table in tables:
        op.execute(f'ALTER TABLE {table} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')


def downgrade() -> None:
    pass
