"""set_default_user_type_for_existing_users

Revision ID: c9c139249b48
Revises: 2fed0ab72c37
Create Date: 2025-06-09 12:16:27.936826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9c139249b48'
down_revision: Union[str, None] = '2fed0ab72c37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set default user_type for existing users who have NULL values
    # Default to 'NORMAL' for existing users
    op.execute("UPDATE users SET user_type = 'NORMAL' WHERE user_type IS NULL")


def downgrade() -> None:
    # Reset user_type to NULL for users who were set to NORMAL
    op.execute("UPDATE users SET user_type = NULL WHERE user_type = 'NORMAL'") 