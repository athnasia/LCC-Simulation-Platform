"""add simulation result column to eng model snapshot

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-04-23 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "g7h8i9j0k1l2"
down_revision = "b3c4d5e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "eng_model_snapshot",
        sa.Column(
            "simulation_result",
            sa.JSON(),
            nullable=True,
            comment="LCC 仿真结果（时间轴事件、总成本、异常信息）",
        ),
    )


def downgrade() -> None:
    op.drop_column("eng_model_snapshot", "simulation_result")