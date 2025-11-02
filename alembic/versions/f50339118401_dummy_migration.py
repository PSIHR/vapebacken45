"""dummy_migration

Revision ID: f50339118401
Revises: None
Create Date: 2025-11-02 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f50339118401'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Dummy upgrade - tables created by SQLAlchemy."""
    pass


def downgrade() -> None:
    """Dummy downgrade."""
    pass
