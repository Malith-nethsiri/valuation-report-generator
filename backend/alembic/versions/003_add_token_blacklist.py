"""Add token_blacklist table for logout functionality.

Revision ID: 003_token_blacklist
Revises: 002_expand_token
Create Date: 2026-02-03

This table stores revoked JWT tokens (by their JTI claim) so that
logout actually invalidates tokens before their natural expiration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_token_blacklist'
down_revision: Union[str, None] = '002_expand_token'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('token_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token_type', sa.String(length=20), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Index for fast JTI lookups (checked on every authenticated request)
    op.create_index(op.f('ix_token_blacklist_jti'), 'token_blacklist', ['jti'], unique=True)
    # Index for cleanup job (delete expired entries)
    op.create_index('ix_token_blacklist_expires_at', 'token_blacklist', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_index(op.f('ix_token_blacklist_jti'), table_name='token_blacklist')
    op.drop_table('token_blacklist')
