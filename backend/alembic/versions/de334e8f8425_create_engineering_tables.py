"""create_engineering_tables

Revision ID: de334e8f8425
Revises: 9ed969162087
Create Date: 2026-04-17 07:12:00.329147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'de334e8f8425'
down_revision: Union[str, Sequence[str], None] = '9ed969162087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建工程建模模块表"""
    # 项目表
    op.create_table('eng_project',
        sa.Column('name', sa.String(length=100), nullable=False, comment='项目名称'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='项目编码'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='项目描述'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_eng_project_code_deleted')
    )
    op.create_index(op.f('ix_eng_project_is_deleted'), 'eng_project', ['is_deleted'], unique=False)

    # 产品表
    op.create_table('eng_product',
        sa.Column('name', sa.String(length=100), nullable=False, comment='产品名称'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='产品编码'),
        sa.Column('project_id', sa.BigInteger(), nullable=False, comment='所属项目 ID'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='产品描述'),
        sa.Column('attributes', sa.JSON(), nullable=True, comment='柔性属性（从基础字典与模板中拉取）'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['project_id'], ['eng_project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_eng_product_code_deleted')
    )
    op.create_index(op.f('ix_eng_product_is_deleted'), 'eng_product', ['is_deleted'], unique=False)

    # 设计方案表
    op.create_table('eng_design_scheme',
        sa.Column('name', sa.String(length=100), nullable=False, comment='方案名称'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='方案编码'),
        sa.Column('product_id', sa.BigInteger(), nullable=False, comment='所属产品 ID'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='方案描述'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['product_id'], ['eng_product.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'is_deleted', name='uq_eng_design_scheme_code_deleted')
    )
    op.create_index(op.f('ix_eng_design_scheme_is_deleted'), 'eng_design_scheme', ['is_deleted'], unique=False)

    # 设计方案版本表
    op.create_table('eng_design_scheme_version',
        sa.Column('scheme_id', sa.BigInteger(), nullable=False, comment='所属方案 ID'),
        sa.Column('version', sa.Integer(), nullable=False, comment='版本号'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态（DRAFT/RELEASED/ARCHIVED）'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='版本描述'),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True, comment='发布时间'),
        sa.Column('released_by', sa.String(length=64), nullable=True, comment='发布人用户 ID'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['scheme_id'], ['eng_design_scheme.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scheme_id', 'version', 'is_deleted', name='uq_eng_design_scheme_version_unique')
    )
    op.create_index(op.f('ix_eng_design_scheme_version_is_deleted'), 'eng_design_scheme_version', ['is_deleted'], unique=False)

    # BOM 节点表
    op.create_table('eng_bom_node',
        sa.Column('scheme_version_id', sa.BigInteger(), nullable=False, comment='所属方案版本 ID'),
        sa.Column('parent_id', sa.BigInteger(), nullable=True, comment='父节点 ID（NULL 表示根节点）'),
        sa.Column('node_name', sa.String(length=100), nullable=False, comment='节点名称'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='节点编码'),
        sa.Column('node_type', sa.String(length=20), nullable=False, comment='节点类型（PART/ASSEMBLY）'),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=True, comment='数量'),
        sa.Column('sort_order', sa.Integer(), nullable=False, comment='排序值'),
        sa.Column('is_configured', sa.Boolean(), server_default='0', nullable=False, comment='是否已配置工艺路线'),
        sa.Column('attributes', sa.JSON(), nullable=True, comment='柔性属性（从基础字典与模板中拉取）'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='节点描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['parent_id'], ['eng_bom_node.id'], ),
        sa.ForeignKeyConstraint(['scheme_version_id'], ['eng_design_scheme_version.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scheme_version_id', 'code', 'is_deleted', name='uq_eng_bom_node_code_unique')
    )
    op.create_index(op.f('ix_eng_bom_node_is_deleted'), 'eng_bom_node', ['is_deleted'], unique=False)

    # 模型快照表
    op.create_table('eng_model_snapshot',
        sa.Column('scheme_version_id', sa.BigInteger(), nullable=False, comment='所属方案版本 ID'),
        sa.Column('snapshot_code', sa.String(length=50), nullable=False, comment='快照编码'),
        sa.Column('snapshot_name', sa.String(length=100), nullable=False, comment='快照名称'),
        sa.Column('snapshot_data', sa.JSON(), nullable=False, comment='快照数据（包含 BOM 树、工艺路线、资源费率等完整信息）'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态（DRAFT/READY/ARCHIVED）'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='快照描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['scheme_version_id'], ['eng_design_scheme_version.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scheme_version_id', 'snapshot_code', 'is_deleted', name='uq_eng_model_snapshot_unique')
    )
    op.create_index(op.f('ix_eng_model_snapshot_is_deleted'), 'eng_model_snapshot', ['is_deleted'], unique=False)

    # 零件工艺路线主表
    op.create_table('eng_component_process_route',
        sa.Column('bom_node_id', sa.BigInteger(), nullable=False, comment='所属 BOM 节点 ID'),
        sa.Column('route_name', sa.String(length=100), nullable=False, comment='路线名称'),
        sa.Column('route_code', sa.String(length=50), nullable=False, comment='路线编码'),
        sa.Column('description', sa.String(length=512), nullable=True, comment='路线描述'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['bom_node_id'], ['eng_bom_node.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bom_node_id', 'route_code', 'is_deleted', name='uq_eng_component_process_route_unique')
    )
    op.create_index(op.f('ix_eng_component_process_route_is_deleted'), 'eng_component_process_route', ['is_deleted'], unique=False)

    # 路线步骤与资源明细表
    op.create_table('eng_route_step_bind',
        sa.Column('route_id', sa.BigInteger(), nullable=False, comment='所属路线 ID'),
        sa.Column('process_id', sa.BigInteger(), nullable=False, comment='标准工艺 ID（来自主数据域）'),
        sa.Column('step_order', sa.Integer(), nullable=False, comment='工序顺序'),
        sa.Column('override_t_set', sa.Numeric(precision=10, scale=4), nullable=True, comment='覆写准备工时（h）'),
        sa.Column('override_t_run', sa.Numeric(precision=10, scale=4), nullable=True, comment='覆写运行工时（h）'),
        sa.Column('override_mat_params', sa.JSON(), nullable=True, comment="覆写辅材参数（如：{'M_T_001': 2.0, 'LIQUID_01': 0.5}）"),
        sa.Column('description', sa.String(length=512), nullable=True, comment='步骤描述'),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后更新时间'),
        sa.Column('created_by', sa.String(length=64), nullable=True, comment='创建人用户 ID'),
        sa.Column('updated_by', sa.String(length=64), nullable=True, comment='最后操作人用户 ID'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='逻辑删除标志（1=已删除）'),
        sa.ForeignKeyConstraint(['process_id'], ['md_process.id'], ),
        sa.ForeignKeyConstraint(['route_id'], ['eng_component_process_route.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route_id', 'step_order', 'is_deleted', name='uq_eng_route_step_bind_unique')
    )
    op.create_index(op.f('ix_eng_route_step_bind_is_deleted'), 'eng_route_step_bind', ['is_deleted'], unique=False)


def downgrade() -> None:
    """删除工程建模模块表"""
    op.drop_index(op.f('ix_eng_route_step_bind_is_deleted'), table_name='eng_route_step_bind')
    op.drop_table('eng_route_step_bind')
    
    op.drop_index(op.f('ix_eng_component_process_route_is_deleted'), table_name='eng_component_process_route')
    op.drop_table('eng_component_process_route')
    
    op.drop_index(op.f('ix_eng_model_snapshot_is_deleted'), table_name='eng_model_snapshot')
    op.drop_table('eng_model_snapshot')
    
    op.drop_index(op.f('ix_eng_bom_node_is_deleted'), table_name='eng_bom_node')
    op.drop_table('eng_bom_node')
    
    op.drop_index(op.f('ix_eng_design_scheme_version_is_deleted'), table_name='eng_design_scheme_version')
    op.drop_table('eng_design_scheme_version')
    
    op.drop_index(op.f('ix_eng_design_scheme_is_deleted'), table_name='eng_design_scheme')
    op.drop_table('eng_design_scheme')
    
    op.drop_index(op.f('ix_eng_product_is_deleted'), table_name='eng_product')
    op.drop_table('eng_product')
    
    op.drop_index(op.f('ix_eng_project_is_deleted'), table_name='eng_project')
    op.drop_table('eng_project')
