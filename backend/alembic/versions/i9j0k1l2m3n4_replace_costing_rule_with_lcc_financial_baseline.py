"""replace costing rule with lcc financial baseline

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-04-23 21:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_eng_costing_rule_is_deleted"), table_name="eng_costing_rule")
    op.drop_table("eng_costing_rule")

    op.create_table(
        "eng_lcc_financial_baseline",
        sa.Column("rule_name", sa.String(length=100), nullable=False, comment="规则名称"),
        sa.Column("lifecycle_years", sa.Integer(), nullable=False, server_default="15", comment="生命周期设定（年）"),
        sa.Column("discount_rate", sa.Numeric(10, 4), nullable=False, server_default="10.0000", comment="资金折现率/WACC（%）"),
        sa.Column("corrosion_rate", sa.Numeric(10, 4), nullable=False, server_default="4.0000", comment="维保年度递增率（%）"),
        sa.Column("risk_strategy", sa.String(length=20), nullable=False, server_default="FIXED", comment="风险拨备策略（FIXED/PERCENTAGE）"),
        sa.Column("risk_value", sa.Numeric(14, 4), nullable=False, server_default="0.0000", comment="风险拨备数值"),
        sa.Column("eol_salvage_rate", sa.Numeric(10, 4), nullable=False, server_default="0.0000", comment="期末残值率（%）"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1", comment="是否启用"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键 ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="最后更新时间"),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人用户 ID"),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="最后操作人用户 ID"),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False, comment="逻辑删除标志（1=已删除）"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_name", "is_deleted", name="uq_eng_lcc_financial_baseline_name_deleted"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(op.f("ix_eng_lcc_financial_baseline_is_deleted"), "eng_lcc_financial_baseline", ["is_deleted"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_eng_lcc_financial_baseline_is_deleted"), table_name="eng_lcc_financial_baseline")
    op.drop_table("eng_lcc_financial_baseline")

    op.create_table(
        "eng_costing_rule",
        sa.Column("rule_name", sa.String(length=100), nullable=False, comment="规则名称"),
        sa.Column("rule_code", sa.String(length=50), nullable=False, comment="规则编码"),
        sa.Column("process_type", sa.String(length=20), nullable=False, server_default="ALL", comment="工艺类型（ALL/IN_HOUSE/OUTSOURCED）"),
        sa.Column("cost_driver", sa.String(length=30), nullable=False, comment="成本驱动因子（MACHINE_HOUR/LABOR_HOUR/MATERIAL_COST/STEP_COUNT）"),
        sa.Column("allocation_method", sa.String(length=20), nullable=False, comment="费用分摊方式（PERCENTAGE/FIXED）"),
        sa.Column("rate_value", sa.Numeric(10, 4), nullable=False, comment="费率值（百分比或固定金额）"),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1", comment="是否启用"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键 ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="最后更新时间"),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人用户 ID"),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="最后操作人用户 ID"),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False, comment="逻辑删除标志（1=已删除）"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code", "is_deleted", name="uq_eng_costing_rule_code_deleted"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(op.f("ix_eng_costing_rule_is_deleted"), "eng_costing_rule", ["is_deleted"], unique=False)