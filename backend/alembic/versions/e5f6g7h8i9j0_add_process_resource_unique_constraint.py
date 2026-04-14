"""add process resource unique constraint

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 md_process_resource 联合唯一索引
    # 防止同一工序重复挂载同一资源
    op.create_unique_constraint(
        'uq_md_process_resource_unique',
        'md_process_resource',
        ['process_id', 'resource_type', 'resource_id', 'is_deleted']
    )


def downgrade() -> None:
    op.drop_constraint('uq_md_process_resource_unique', 'md_process_resource', type_='unique')
