"""Expand password_reset_token column for bcrypt hashes.

Revision ID: 002_expand_token
Revises: 001_baseline
Create Date: 2026-02-03

Bcrypt hashes are ~60 characters, so we need more than 100 chars.
This migration also invalidates any existing plaintext tokens (acceptable
since they expire in 1 hour anyway).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_expand_token'
down_revision: Union[str, None] = '001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand column to accommodate bcrypt hashes (~60 chars)
    op.alter_column('users', 'password_reset_token',
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=255),
                    existing_nullable=True)

    # Invalidate any existing plaintext tokens by setting them to NULL
    # This is safe because tokens expire in 1 hour anyway
    op.execute("UPDATE users SET password_reset_token = NULL, password_reset_expires = NULL WHERE password_reset_token IS NOT NULL")


def downgrade() -> None:
    # Clear any hashed tokens before shrinking column
    op.execute("UPDATE users SET password_reset_token = NULL, password_reset_expires = NULL WHERE password_reset_token IS NOT NULL")

    op.alter_column('users', 'password_reset_token',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=100),
                    existing_nullable=True)
