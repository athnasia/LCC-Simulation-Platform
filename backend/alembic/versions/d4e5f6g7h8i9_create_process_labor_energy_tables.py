"""create process labor energy tables

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════════════════
    # 1. 更新 md_material 表（添加进阶字段）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.add_column('md_material', sa.Column('unit_price', sa.Numeric(10, 4), nullable=True, comment='单价（元/计价单位）'))
    op.add_column('md_material', sa.Column('loss_rate', sa.Numeric(5, 2), nullable=True, comment='变动损耗率（%）'))
    op.add_column('md_material', sa.Column('scrap_value', sa.Numeric(10, 4), nullable=True, comment='废料回收残值（元/单位）'))
    op.add_column('md_material', sa.Column('substitute_group', sa.String(50), nullable=True, comment='替代料群组编码'))
    op.add_column('md_material', sa.Column('substitute_priority', sa.Integer, nullable=True, comment='替代优先级'))
    op.add_column('md_material', sa.Column('lcc_lifespan_months', sa.Integer, nullable=True, comment='理论疲劳寿命（月）'))
    op.add_column('md_material', sa.Column('lcc_maintenance_cost', sa.Numeric(10, 2), nullable=True, comment='单次维保预估成本（元）'))

    # 修改外键类型为 BigInteger
    op.alter_column('md_material', 'category_id', existing_type=sa.Integer, type_=sa.BigInteger, existing_nullable=True)
    op.alter_column('md_material', 'pricing_unit_id', existing_type=sa.Integer, type_=sa.BigInteger, existing_nullable=True)
    op.alter_column('md_material', 'consumption_unit_id', existing_type=sa.Integer, type_=sa.BigInteger, existing_nullable=True)

    # ═══════════════════════════════════════════════════════════════════════════════
    # 2. 更新 md_equipment 表（添加仿真约束字段）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.add_column('md_equipment', sa.Column('setup_cost', sa.Numeric(10, 2), nullable=True, comment='换型成本（元/次）'))
    op.add_column('md_equipment', sa.Column('oee_target', sa.Numeric(5, 2), nullable=True, comment='目标 OEE（%）'))
    op.add_column('md_equipment', sa.Column('mtbf_hours', sa.Numeric(10, 2), nullable=True, comment='平均无故障时间 MTBF（小时）'))
    op.add_column('md_equipment', sa.Column('defect_rate', sa.Numeric(5, 4), nullable=True, comment='标准缺陷率（%）'))

    # 修改外键类型为 BigInteger
    op.alter_column('md_equipment', 'category_id', existing_type=sa.Integer, type_=sa.BigInteger, existing_nullable=True)

    # ═══════════════════════════════════════════════════════════════════════════════
    # 3. 创建 md_process 表（标准工艺/工时库）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.create_table(
        'md_process',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='工序名称'),
        sa.Column('code', sa.String(50), nullable=False, comment='工序编码（变量标识）'),
        sa.Column('category_id', sa.BigInteger, nullable=True, comment='工序分类 ID'),
        sa.Column('standard_time', sa.Numeric(10, 4), nullable=True, comment='标准工时（小时）'),
        sa.Column('setup_time', sa.Numeric(10, 4), nullable=True, comment='换产准备时间（小时）'),
        sa.Column('is_active', sa.Boolean, server_default='1', comment='是否启用'),
        sa.Column('description', sa.String(512), nullable=True, comment='工序描述'),
        sa.Column('is_deleted', sa.Boolean, server_default='0', comment='逻辑删除标记'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.Column('created_by', sa.String(50), nullable=True, comment='创建人'),
        sa.Column('updated_by', sa.String(50), nullable=True, comment='更新人'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_process_code_deleted'),
        sa.ForeignKeyConstraint(['category_id'], ['md_resource_category.id'], name='fk_md_process_category'),
    )
    op.create_index('ix_md_process_is_deleted', 'md_process', ['is_deleted'])
    op.create_index('ix_md_process_category_id', 'md_process', ['category_id'])
    op.create_index('ix_md_process_is_active', 'md_process', ['is_active'])

    # ═══════════════════════════════════════════════════════════════════════════════
    # 4. 创建 md_process_resource 表（工艺资源挂载包）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.create_table(
        'md_process_resource',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column('process_id', sa.BigInteger, nullable=False, comment='工序 ID'),
        sa.Column('resource_type', sa.Enum('MATERIAL', 'EQUIPMENT', 'LABOR', 'TOOL', name='resourcetype'), nullable=False, comment='资源类型'),
        sa.Column('resource_id', sa.BigInteger, nullable=False, comment='资源 ID'),
        sa.Column('quantity', sa.Numeric(10, 4), server_default='1', comment='消耗数量/投入比例'),
        sa.Column('description', sa.String(256), nullable=True, comment='备注说明'),
        sa.Column('is_deleted', sa.Boolean, server_default='0', comment='逻辑删除标记'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.Column('created_by', sa.String(50), nullable=True, comment='创建人'),
        sa.Column('updated_by', sa.String(50), nullable=True, comment='更新人'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['process_id'], ['md_process.id'], name='fk_md_process_resource_process'),
    )
    op.create_index('ix_md_process_resource_process_id', 'md_process_resource', ['process_id'])
    op.create_index('ix_md_process_resource_type', 'md_process_resource', ['resource_type'])

    # ═══════════════════════════════════════════════════════════════════════════════
    # 5. 创建 md_labor 表（人员技能资质矩阵）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.create_table(
        'md_labor',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='人员名称'),
        sa.Column('code', sa.String(50), nullable=False, comment='人员编码'),
        sa.Column('labor_type', sa.String(50), nullable=True, comment='工种'),
        sa.Column('skill_level', sa.Enum('JUNIOR', 'INTERMEDIATE', 'SENIOR', 'MASTER', name='skilllevel'), nullable=False, comment='技能等级'),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True, comment='标准时薪（元/小时）'),
        sa.Column('qualification_code', sa.String(50), nullable=True, comment='资质编码'),
        sa.Column('category_id', sa.BigInteger, nullable=True, comment='人员分类 ID'),
        sa.Column('is_active', sa.Boolean, server_default='1', comment='是否启用'),
        sa.Column('description', sa.String(512), nullable=True, comment='人员描述'),
        sa.Column('is_deleted', sa.Boolean, server_default='0', comment='逻辑删除标记'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.Column('created_by', sa.String(50), nullable=True, comment='创建人'),
        sa.Column('updated_by', sa.String(50), nullable=True, comment='更新人'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_labor_code_deleted'),
        sa.ForeignKeyConstraint(['category_id'], ['md_resource_category.id'], name='fk_md_labor_category'),
    )
    op.create_index('ix_md_labor_is_deleted', 'md_labor', ['is_deleted'])
    op.create_index('ix_md_labor_category_id', 'md_labor', ['category_id'])
    op.create_index('ix_md_labor_skill_level', 'md_labor', ['skill_level'])
    op.create_index('ix_md_labor_is_active', 'md_labor', ['is_active'])

    # ═══════════════════════════════════════════════════════════════════════════════
    # 6. 创建 md_energy_rate 表（能源单价）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.create_table(
        'md_energy_rate',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='能源名称'),
        sa.Column('code', sa.String(50), nullable=False, comment='能源编码'),
        sa.Column('energy_type', sa.Enum('ELECTRICITY', 'WATER', 'GAS', 'STEAM', 'COMPRESSED_AIR', name='energytype'), nullable=False, comment='能源类型'),
        sa.Column('unit_price', sa.Numeric(10, 4), nullable=False, comment='单价（元/单位）'),
        sa.Column('unit_id', sa.BigInteger, nullable=True, comment='计价单位 ID'),
        sa.Column('is_active', sa.Boolean, server_default='1', comment='是否启用'),
        sa.Column('description', sa.String(256), nullable=True, comment='能源描述'),
        sa.Column('is_deleted', sa.Boolean, server_default='0', comment='逻辑删除标记'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.Column('created_by', sa.String(50), nullable=True, comment='创建人'),
        sa.Column('updated_by', sa.String(50), nullable=True, comment='更新人'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_md_energy_rate_code_deleted'),
        sa.ForeignKeyConstraint(['unit_id'], ['md_unit.id'], name='fk_md_energy_rate_unit'),
    )
    op.create_index('ix_md_energy_rate_is_deleted', 'md_energy_rate', ['is_deleted'])
    op.create_index('ix_md_energy_rate_energy_type', 'md_energy_rate', ['energy_type'])
    op.create_index('ix_md_energy_rate_is_active', 'md_energy_rate', ['is_active'])

    # ═══════════════════════════════════════════════════════════════════════════════
    # 7. 创建 md_energy_calendar 表（能源日历）
    # ═══════════════════════════════════════════════════════════════════════════════
    op.create_table(
        'md_energy_calendar',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column('energy_rate_id', sa.BigInteger, nullable=False, comment='能源单价 ID'),
        sa.Column('name', sa.String(50), nullable=False, comment='时段名称'),
        sa.Column('start_time', sa.Time, nullable=False, comment='开始时间'),
        sa.Column('end_time', sa.Time, nullable=False, comment='结束时间'),
        sa.Column('multiplier', sa.Numeric(5, 2), server_default='1.0', comment='费率系数'),
        sa.Column('is_active', sa.Boolean, server_default='1', comment='是否启用'),
        sa.Column('description', sa.String(256), nullable=True, comment='时段描述'),
        sa.Column('is_deleted', sa.Boolean, server_default='0', comment='逻辑删除标记'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.Column('created_by', sa.String(50), nullable=True, comment='创建人'),
        sa.Column('updated_by', sa.String(50), nullable=True, comment='更新人'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['energy_rate_id'], ['md_energy_rate.id'], name='fk_md_energy_calendar_rate'),
    )
    op.create_index('ix_md_energy_calendar_energy_rate_id', 'md_energy_calendar', ['energy_rate_id'])
    op.create_index('ix_md_energy_calendar_is_active', 'md_energy_calendar', ['is_active'])


def downgrade() -> None:
    op.drop_table('md_energy_calendar')
    op.drop_table('md_energy_rate')
    op.drop_table('md_labor')
    op.drop_table('md_process_resource')
    op.drop_table('md_process')

    # 删除 md_equipment 新增字段
    op.drop_column('md_equipment', 'defect_rate')
    op.drop_column('md_equipment', 'mtbf_hours')
    op.drop_column('md_equipment', 'oee_target')
    op.drop_column('md_equipment', 'setup_cost')

    # 删除 md_material 新增字段
    op.drop_column('md_material', 'lcc_maintenance_cost')
    op.drop_column('md_material', 'lcc_lifespan_months')
    op.drop_column('md_material', 'substitute_priority')
    op.drop_column('md_material', 'substitute_group')
    op.drop_column('md_material', 'scrap_value')
    op.drop_column('md_material', 'loss_rate')
    op.drop_column('md_material', 'unit_price')
