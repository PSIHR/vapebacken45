"""add_postal_delivery_fields

Revision ID: a1b2c3d4e5f6
Revises: 5f18606091ad
Create Date: 2025-11-02 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5f18606091ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add postal delivery fields to orders table."""
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('postal_full_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('postal_phone', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('postal_address', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('postal_index', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove postal delivery fields from orders table."""
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('postal_index')
        batch_op.drop_column('postal_address')
        batch_op.drop_column('postal_phone')
        batch_op.drop_column('postal_full_name')
