"""create_material_and_equipment_tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-04-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建材料表和设备表"""
    
    # ── 1. 材料主数据表 ───────────────────────────────────────────────────────────
    op.create_table(
        'md_material',
        sa.Column('name', sa.String(100), nullable=False, comment='材料名称'),
        sa.Column('code', sa.String(50), nullable=False, comment='材料编码'),
        sa.Column('category_id', sa.BigInteger(), nullable=True, comment='材料分类 ID'),
        sa.Column('pricing_unit_id', sa.BigInteger(), nullable=True, comment='计价单位 ID'),
        sa.Column('consumption_unit_id', sa.BigInteger(), nullable=True, comment='消耗单位 ID'),
        sa.Column('dynamic_attributes', sa.JSON(), nullable=True, comment='柔性属性'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('description', sa.String(512), nullable=True, comment='材料描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.ForeignKeyConstraint(['category_id'], ['md_resource_category.id'], ),
        sa.ForeignKeyConstraint(['pricing_unit_id'], ['md_unit.id'], ),
        sa.ForeignKeyConstraint(['consumption_unit_id'], ['md_unit.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_material_code_deleted'),
    )
    op.create_index(op.f('ix_md_material_is_deleted'), 'md_material', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_md_material_category_id'), 'md_material', ['category_id'], unique=False)
    op.create_index(op.f('ix_md_material_is_active'), 'md_material', ['is_active'], unique=False)

    # ── 2. 设备主数据表 ───────────────────────────────────────────────────────────
    op.create_table(
        'md_equipment',
        sa.Column('name', sa.String(100), nullable=False, comment='设备名称'),
        sa.Column('code', sa.String(50), nullable=False, comment='设备编码'),
        sa.Column('category_id', sa.BigInteger(), nullable=True, comment='设备分类 ID'),
        sa.Column('depreciation_rate', sa.Numeric(10, 4), nullable=True, comment='静态折旧费率'),
        sa.Column('power_consumption', sa.Numeric(10, 4), nullable=True, comment='基础能耗系数'),
        sa.Column('dynamic_attributes', sa.JSON(), nullable=True, comment='柔性属性'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('description', sa.String(512), nullable=True, comment='设备描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志'),
        sa.ForeignKeyConstraint(['category_id'], ['md_resource_category.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_equipment_code_deleted'),
    )
    op.create_index(op.f('ix_md_equipment_is_deleted'), 'md_equipment', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_md_equipment_category_id'), 'md_equipment', ['category_id'], unique=False)
    op.create_index(op.f('ix_md_equipment_is_active'), 'md_equipment', ['is_active'], unique=False)


def downgrade() -> None:
    """删除材料表和设备表"""
    op.drop_index(op.f('ix_md_equipment_is_active'), table_name='md_equipment')
    op.drop_index(op.f('ix_md_equipment_category_id'), table_name='md_equipment')
    op.drop_index(op.f('ix_md_equipment_is_deleted'), table_name='md_equipment')
    op.drop_table('md_equipment')
    
    op.drop_index(op.f('ix_md_material_is_active'), table_name='md_material')
    op.drop_index(op.f('ix_md_material_category_id'), table_name='md_material')
    op.drop_index(op.f('ix_md_material_is_deleted'), table_name='md_material')
    op.drop_table('md_material')
