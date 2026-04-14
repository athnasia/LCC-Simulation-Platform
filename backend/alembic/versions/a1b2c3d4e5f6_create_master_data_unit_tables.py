"""create_master_data_unit_tables

Revision ID: a1b2c3d4e5f6
Revises: 7c1f1a2c4d5e
Create Date: 2026-04-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7c1f1a2c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建主数据域基础表：量纲、单位、单位换算"""
    
    # ── 1. 量纲定义表 ───────────────────────────────────────────────────────────
    op.create_table(
        'md_unit_dimension',
        sa.Column('name', sa.String(50), nullable=False, comment='量纲名称'),
        sa.Column('code', sa.String(30), nullable=False, comment='量纲编码'),
        sa.Column('description', sa.String(256), nullable=True, comment='量纲描述'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序值'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_unit_dimension_code_deleted'),
    )
    op.create_index(op.f('ix_md_unit_dimension_is_deleted'), 'md_unit_dimension', ['is_deleted'], unique=False)

    # ── 2. 单位表 ───────────────────────────────────────────────────────────────
    op.create_table(
        'md_unit',
        sa.Column('name', sa.String(50), nullable=False, comment='单位名称'),
        sa.Column('code', sa.String(20), nullable=False, comment='单位编码'),
        sa.Column('symbol', sa.String(10), nullable=True, comment='单位符号'),
        sa.Column('dimension_id', sa.BigInteger(), nullable=False, comment='所属量纲 ID'),
        sa.Column('is_base', sa.Boolean(), server_default='0', nullable=False, comment='是否基础单位'),
        sa.Column('description', sa.String(256), nullable=True, comment='单位描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.ForeignKeyConstraint(['dimension_id'], ['md_unit_dimension.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_unit_code_deleted'),
    )
    op.create_index(op.f('ix_md_unit_is_deleted'), 'md_unit', ['is_deleted'], unique=False)

    # ── 3. 单位换算表 ───────────────────────────────────────────────────────────
    op.create_table(
        'md_unit_conversion',
        sa.Column('from_unit_id', sa.BigInteger(), nullable=False, comment='源单位 ID'),
        sa.Column('to_unit_id', sa.BigInteger(), nullable=False, comment='目标单位 ID'),
        sa.Column('conversion_factor', sa.Numeric(20, 10), nullable=False, comment='换算因子'),
        sa.Column('offset', sa.Numeric(20, 10), nullable=True, comment='偏移量'),
        sa.Column('description', sa.String(256), nullable=True, comment='换算说明'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.ForeignKeyConstraint(['from_unit_id'], ['md_unit.id'], ),
        sa.ForeignKeyConstraint(['to_unit_id'], ['md_unit.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('from_unit_id', 'to_unit_id', 'is_deleted', name='uq_md_unit_conversion_pair_deleted'),
    )
    op.create_index(op.f('ix_md_unit_conversion_is_deleted'), 'md_unit_conversion', ['is_deleted'], unique=False)


def downgrade() -> None:
    """删除主数据域基础表"""
    op.drop_index(op.f('ix_md_unit_conversion_is_deleted'), table_name='md_unit_conversion')
    op.drop_table('md_unit_conversion')
    
    op.drop_index(op.f('ix_md_unit_is_deleted'), table_name='md_unit')
    op.drop_table('md_unit')
    
    op.drop_index(op.f('ix_md_unit_dimension_is_deleted'), table_name='md_unit_dimension')
    op.drop_table('md_unit_dimension')
