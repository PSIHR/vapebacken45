"""add_delivery_time_and_cost_fields

Revision ID: 0bd332ec95cc
Revises: 
Create Date: 2025-11-01 18:38:14.875556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bd332ec95cc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('preferred_time', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('time_slot', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('delivery_cost', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'delivery_cost')
    op.drop_column('orders', 'time_slot')
    op.drop_column('orders', 'preferred_time')
