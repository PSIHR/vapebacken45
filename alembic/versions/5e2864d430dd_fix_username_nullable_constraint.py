"""fix username nullable constraint

Revision ID: 5e2864d430dd
Revises:
Create Date: 2025-08-14 15:59:45.531768

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5e2864d430dd"
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
