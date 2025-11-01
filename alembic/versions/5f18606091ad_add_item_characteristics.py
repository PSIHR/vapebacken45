"""add_item_characteristics

Revision ID: 5f18606091ad
Revises: 196b190e0477
Create Date: 2025-11-01 20:05:37.361904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f18606091ad'
down_revision: Union[str, Sequence[str], None] = '196b190e0477'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.add_column(sa.Column('strength', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('puffs', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('vg_pg', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('tank_volume', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.drop_column('tank_volume')
        batch_op.drop_column('vg_pg')
        batch_op.drop_column('puffs')
        batch_op.drop_column('strength')
