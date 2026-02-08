"""Add email verification fields to users table.

Revision ID: 005_email_verification
Revises: 004_add_indexes
Create Date: 2026-02-06

Adds fields for email verification:
- email_verified: Boolean flag (default False for new users)
- email_verification_token: Hashed token for verification links
- email_verification_expires: Token expiration timestamp

Existing users are grandfathered as verified to prevent lockout.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_email_verification'
down_revision: Union[str, None] = '004_add_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email verification columns
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True))

    # Remove server_default after migration (new users will get False from model default)
    op.alter_column('users', 'email_verified', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'email_verification_expires')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
