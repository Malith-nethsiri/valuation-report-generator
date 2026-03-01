"""Add security constraints: junction table unique constraints and vehicle soft-delete partial index.

Revision ID: 007_security_constraints
Revises: 006_oauth_fields
Create Date: 2026-02-25

Changes:
- S5: Add UniqueConstraint on (report_id, property_id) for report_properties table
- S5: Add UniqueConstraint on (report_id, vehicle_id) for report_vehicles table
- S6: Replace the Vehicle user+registration unique constraint with a partial unique
      index that excludes soft-deleted rows, so deleted vehicles do not block
      re-registration of the same plate number.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_security_constraints'
down_revision: Union[str, None] = '006_oauth_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # S5: Unique constraint — a property can appear in a given report only once
    op.create_unique_constraint(
        'uq_report_properties_report_property',
        'report_properties',
        ['report_id', 'property_id']
    )

    # S5: Unique constraint — a vehicle can appear in a given report only once
    op.create_unique_constraint(
        'uq_report_vehicles_report_vehicle',
        'report_vehicles',
        ['report_id', 'vehicle_id']
    )

    # S6: Drop the full unique constraint that blocks re-registration after soft-delete
    op.drop_constraint('uq_vehicle_user_registration', 'vehicles', type_='unique')

    # S6: Partial unique index — enforces uniqueness only among non-deleted vehicles
    op.create_index(
        'uq_vehicle_user_registration_active',
        'vehicles',
        ['user_id', 'registration_number'],
        unique=True,
        postgresql_where=sa.text('is_deleted IS NOT TRUE')
    )


def downgrade() -> None:
    op.drop_index('uq_vehicle_user_registration_active', table_name='vehicles')

    op.create_unique_constraint(
        'uq_vehicle_user_registration',
        'vehicles',
        ['user_id', 'registration_number']
    )

    op.drop_constraint('uq_report_vehicles_report_vehicle', 'report_vehicles', type_='unique')
    op.drop_constraint('uq_report_properties_report_property', 'report_properties', type_='unique')
