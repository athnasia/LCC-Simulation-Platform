"""soft_delete_unique_constraints

Revision ID: 7c1f1a2c4d5e
Revises: df78acee9fdf
Create Date: 2026-04-15 00:40:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7c1f1a2c4d5e"
down_revision: Union[str, Sequence[str], None] = "df78acee9fdf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("code", "org_department", type_="unique")
    op.create_unique_constraint("uq_org_department_code_deleted", "org_department", ["code", "is_deleted"])

    op.drop_constraint("username", "sys_user", type_="unique")
    op.drop_constraint("email", "sys_user", type_="unique")
    op.create_unique_constraint("uq_sys_user_username_deleted", "sys_user", ["username", "is_deleted"])
    op.create_unique_constraint("uq_sys_user_email_deleted", "sys_user", ["email", "is_deleted"])

    op.drop_constraint("code", "sys_role", type_="unique")
    op.drop_constraint("name", "sys_role", type_="unique")
    op.create_unique_constraint("uq_sys_role_code_deleted", "sys_role", ["code", "is_deleted"])
    op.create_unique_constraint("uq_sys_role_name_deleted", "sys_role", ["name", "is_deleted"])

    op.drop_constraint("code", "sys_permission", type_="unique")
    op.create_unique_constraint("uq_sys_permission_code_deleted", "sys_permission", ["code", "is_deleted"])


def downgrade() -> None:
    op.drop_constraint("uq_sys_permission_code_deleted", "sys_permission", type_="unique")
    op.create_unique_constraint("code", "sys_permission", ["code"])

    op.drop_constraint("uq_sys_role_name_deleted", "sys_role", type_="unique")
    op.drop_constraint("uq_sys_role_code_deleted", "sys_role", type_="unique")
    op.create_unique_constraint("name", "sys_role", ["name"])
    op.create_unique_constraint("code", "sys_role", ["code"])

    op.drop_constraint("uq_sys_user_email_deleted", "sys_user", type_="unique")
    op.drop_constraint("uq_sys_user_username_deleted", "sys_user", type_="unique")
    op.create_unique_constraint("email", "sys_user", ["email"])
    op.create_unique_constraint("username", "sys_user", ["username"])

    op.drop_constraint("uq_org_department_code_deleted", "org_department", type_="unique")
    op.create_unique_constraint("code", "org_department", ["code"])