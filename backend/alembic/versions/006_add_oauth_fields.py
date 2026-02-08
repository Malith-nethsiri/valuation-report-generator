"""Add OAuth fields to users table.

Revision ID: 006_oauth_fields
Revises: 005_email_verification
Create Date: 2026-02-06

Adds fields for OAuth authentication:
- google_id: Unique Google account identifier
- oauth_provider: Which OAuth provider was used (google, etc.)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_oauth_fields'
down_revision: Union[str, None] = '005_email_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add OAuth columns
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))

    # Create unique index on google_id for fast lookups
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'google_id')
