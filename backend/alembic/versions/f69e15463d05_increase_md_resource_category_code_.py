"""increase md_resource_category code length

Revision ID: f69e15463d05
Revises: 1a2b3c4d5e6f
Create Date: 2026-04-15 17:51:06.732219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'f69e15463d05'
down_revision: Union[str, Sequence[str], None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('md_resource_category', 'code',
               existing_type=mysql.VARCHAR(length=30),
               type_=sa.String(length=50),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('md_resource_category', 'code',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.String(length=30),
               existing_nullable=False)
