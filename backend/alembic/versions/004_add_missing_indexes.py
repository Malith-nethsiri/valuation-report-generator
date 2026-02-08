"""Add missing indexes for query performance.

Revision ID: 004_add_indexes
Revises: 003_token_blacklist
Create Date: 2026-02-03

Indexes added:
- reports.report_type - for filtering by report type
- reports.status - for filtering by status (draft/completed)
- reports.created_at - for sorting/pagination by date
- report_vehicles.report_id - for joining reports to vehicles
- report_vehicles.vehicle_id - for joining vehicles to reports
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_add_indexes'
down_revision: Union[str, None] = '003_token_blacklist'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reports table indexes
    op.create_index('ix_reports_report_type', 'reports', ['report_type'], unique=False)
    op.create_index('ix_reports_status', 'reports', ['status'], unique=False)
    op.create_index('ix_reports_created_at', 'reports', ['created_at'], unique=False)

    # ReportVehicles junction table indexes
    op.create_index('ix_report_vehicles_report_id', 'report_vehicles', ['report_id'], unique=False)
    op.create_index('ix_report_vehicles_vehicle_id', 'report_vehicles', ['vehicle_id'], unique=False)


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('ix_report_vehicles_vehicle_id', table_name='report_vehicles')
    op.drop_index('ix_report_vehicles_report_id', table_name='report_vehicles')
    op.drop_index('ix_reports_created_at', table_name='reports')
    op.drop_index('ix_reports_status', table_name='reports')
    op.drop_index('ix_reports_report_type', table_name='reports')
