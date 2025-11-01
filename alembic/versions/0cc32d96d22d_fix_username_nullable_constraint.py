"""fix username nullable constraint

Revision ID: 0cc32d96d22d
Revises:
Create Date: 2025-08-14 16:06:06.707847

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0cc32d96d22d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Для SQLite требуется специальный подход
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column("username", nullable=True)


def downgrade():
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column("username", nullable=False)
