"""Set default values for is_ended field

Revision ID: 860aab090ee0
Revises: 6d44727e5661
Create Date: 2025-05-28 13:11:36.575744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '860aab090ee0'
down_revision: Union[str, None] = '6d44727e5661'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing meetings with NULL is_ended values to False
    op.execute("UPDATE meetings SET is_ended = false WHERE is_ended IS NULL")


def downgrade() -> None:
    # No downgrade needed for this data migration
    pass
