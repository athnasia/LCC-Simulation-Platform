"""create_resource_category_and_attr_tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建资源分类表和属性定义表"""
    
    # ── 1. 资源分类表 ───────────────────────────────────────────────────────────
    op.create_table(
        'md_resource_category',
        sa.Column('name', sa.String(50), nullable=False, comment='分类名称'),
        sa.Column('code', sa.String(30), nullable=False, comment='分类编码'),
        sa.Column('resource_type', sa.Enum('MATERIAL', 'EQUIPMENT', 'LABOR', 'TOOL'), nullable=False, comment='资源类型'),
        sa.Column('parent_id', sa.BigInteger(), nullable=True, comment='父分类 ID（自关联）'),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False, comment='排序值'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('description', sa.String(256), nullable=True, comment='分类描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.ForeignKeyConstraint(['parent_id'], ['md_resource_category.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_resource_category_code_deleted'),
    )
    op.create_index(op.f('ix_md_resource_category_is_deleted'), 'md_resource_category', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_md_resource_category_parent_id'), 'md_resource_category', ['parent_id'], unique=False)
    op.create_index(op.f('ix_md_resource_category_resource_type'), 'md_resource_category', ['resource_type'], unique=False)

    # ── 2. 属性定义表 ───────────────────────────────────────────────────────────
    op.create_table(
        'md_attr_definition',
        sa.Column('name', sa.String(50), nullable=False, comment='属性名称'),
        sa.Column('code', sa.String(30), nullable=False, comment='变量标识码'),
        sa.Column('data_type', sa.Enum('STRING', 'NUMBER', 'BOOLEAN', 'JSON', 'DATE', 'ENUM'), nullable=False, comment='数据类型'),
        sa.Column('unit_id', sa.BigInteger(), nullable=True, comment='关联单位 ID'),
        sa.Column('applicable_resource_types', sa.JSON(), nullable=True, comment='适用资源类型'),
        sa.Column('description', sa.String(256), nullable=True, comment='属性描述'),
        sa.Column('is_required', sa.Boolean(), server_default='0', nullable=False, comment='是否必填'),
        sa.Column('default_value', sa.Text(), nullable=True, comment='默认值'),
        sa.Column('enum_values', sa.JSON(), nullable=True, comment='枚举值列表'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.ForeignKeyConstraint(['unit_id'], ['md_unit.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_attr_definition_code_deleted'),
    )
    op.create_index(op.f('ix_md_attr_definition_is_deleted'), 'md_attr_definition', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_md_attr_definition_data_type'), 'md_attr_definition', ['data_type'], unique=False)
    op.create_index(op.f('ix_md_attr_definition_unit_id'), 'md_attr_definition', ['unit_id'], unique=False)


def downgrade() -> None:
    """删除资源分类表和属性定义表"""
    op.drop_index(op.f('ix_md_attr_definition_unit_id'), table_name='md_attr_definition')
    op.drop_index(op.f('ix_md_attr_definition_data_type'), table_name='md_attr_definition')
    op.drop_index(op.f('ix_md_attr_definition_is_deleted'), table_name='md_attr_definition')
    op.drop_table('md_attr_definition')
    
    op.drop_index(op.f('ix_md_resource_category_resource_type'), table_name='md_resource_category')
    op.drop_index(op.f('ix_md_resource_category_parent_id'), table_name='md_resource_category')
    op.drop_index(op.f('ix_md_resource_category_is_deleted'), table_name='md_resource_category')
    op.drop_table('md_resource_category')
