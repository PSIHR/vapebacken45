"""merge branches

Revision ID: 916ce5b4a676
Revises: 0cc32d96d22d
Create Date: 2025-08-14 16:23:46.513682

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "916ce5b4a676"
down_revision: Union[str, Sequence[str], None] = "0cc32d96d22d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
