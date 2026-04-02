"""Add vehicle book_data, spec_data, variant, spec_source, spec_confidence columns.

Revision ID: 008_vehicle_book_spec_data
Revises: 007_security_constraints
Create Date: 2026-03-06

Changes:
- Add variant column (String 100, nullable) for trim/grade level
- Add book_data column (JSON, nullable) for all OCR-extracted CR Book fields
- Add spec_data column (JSON, nullable) for AI-enriched manufacturer specifications
- Add spec_source column (String 50, nullable) for spec data source tracking
- Add spec_confidence column (Numeric 3,2, nullable) for spec confidence score
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_vehicle_book_spec_data'
down_revision: Union[str, None] = '007_security_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vehicles', sa.Column('variant', sa.String(100), nullable=True))
    op.add_column('vehicles', sa.Column('book_data', sa.JSON(), nullable=True))
    op.add_column('vehicles', sa.Column('spec_data', sa.JSON(), nullable=True))
    op.add_column('vehicles', sa.Column('spec_source', sa.String(50), nullable=True))
    op.add_column('vehicles', sa.Column('spec_confidence', sa.Numeric(3, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('vehicles', 'spec_confidence')
    op.drop_column('vehicles', 'spec_source')
    op.drop_column('vehicles', 'spec_data')
    op.drop_column('vehicles', 'book_data')
    op.drop_column('vehicles', 'variant')
