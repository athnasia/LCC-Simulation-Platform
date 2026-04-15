"""create_system_dictionary_tables

Revision ID: 1a2b3c4d5e6f
Revises: f6g7h8i9j0k1
Create Date: 2026-04-15 22:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "f6g7h8i9j0k1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sys_dict_type",
        sa.Column("name", sa.String(length=64), nullable=False, comment="字典类型名称"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="字典类型编码"),
        sa.Column("description", sa.String(length=256), nullable=True, comment="字典类型描述"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="排序值，升序"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1", comment="是否启用"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键 ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="最后更新时间"),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人用户 ID"),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="最后操作人用户 ID"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0", comment="逻辑删除标志（1=已删除）"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "is_deleted", name="uq_sys_dict_type_code_deleted"),
        mysql_charset="utf8mb4",
    )
    op.create_index(op.f("ix_sys_dict_type_is_deleted"), "sys_dict_type", ["is_deleted"], unique=False)

    op.create_table(
        "sys_dict_item",
        sa.Column("dict_type_id", sa.BigInteger(), nullable=False, comment="所属字典类型 ID"),
        sa.Column("value", sa.String(length=100), nullable=False, comment="存储值，保持原始枚举或编码"),
        sa.Column("label", sa.String(length=100), nullable=False, comment="展示标签"),
        sa.Column("description", sa.String(length=256), nullable=True, comment="字典项描述"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="排序值，升序"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1", comment="是否启用"),
        sa.Column("extra_json", mysql.JSON(), nullable=True, comment="扩展元数据"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键 ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="最后更新时间"),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人用户 ID"),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="最后操作人用户 ID"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0", comment="逻辑删除标志（1=已删除）"),
        sa.ForeignKeyConstraint(["dict_type_id"], ["sys_dict_type.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dict_type_id", "value", "is_deleted", name="uq_sys_dict_item_type_value_deleted"),
        mysql_charset="utf8mb4",
    )
    op.create_index(op.f("ix_sys_dict_item_is_deleted"), "sys_dict_item", ["is_deleted"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sys_dict_item_is_deleted"), table_name="sys_dict_item")
    op.drop_table("sys_dict_item")
    op.drop_index(op.f("ix_sys_dict_type_is_deleted"), table_name="sys_dict_type")
    op.drop_table("sys_dict_type")