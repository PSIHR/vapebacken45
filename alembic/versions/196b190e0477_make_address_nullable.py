"""make_address_nullable

Revision ID: 196b190e0477
Revises: 0bd332ec95cc
Create Date: 2025-11-01 18:41:56.863172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '196b190e0477'
down_revision: Union[str, Sequence[str], None] = '0bd332ec95cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('orders') as batch_op:
        batch_op.alter_column('address', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('orders') as batch_op:
        batch_op.alter_column('address', nullable=False)
