"""Add admin_logs and system_metrics tables

Revision ID: 001_add_admin_logs
Revises:
Create Date: 2024-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_admin_logs'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create log_level enum
    log_level_enum = postgresql.ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='loglevel', create_type=False)
    log_level_enum.create(op.get_bind(), checkfirst=True)

    # Create action_type enum
    action_type_enum = postgresql.ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'IMPORT', 'SYSTEM', name='actiontype', create_type=False)
    action_type_enum.create(op.get_bind(), checkfirst=True)

    # Create admin_logs table
    op.create_table(
        'admin_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('action', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'IMPORT', 'SYSTEM', name='actiontype'), nullable=False),
        sa.Column('level', sa.Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='loglevel'), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_logs_action'), 'admin_logs', ['action'], unique=False)
    op.create_index(op.f('ix_admin_logs_created_at'), 'admin_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_admin_logs_id'), 'admin_logs', ['id'], unique=False)
    op.create_index(op.f('ix_admin_logs_level'), 'admin_logs', ['level'], unique=False)
    op.create_index(op.f('ix_admin_logs_resource_type'), 'admin_logs', ['resource_type'], unique=False)

    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_metrics_id'), 'system_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_system_metrics_metric_name'), 'system_metrics', ['metric_name'], unique=False)
    op.create_index(op.f('ix_system_metrics_recorded_at'), 'system_metrics', ['recorded_at'], unique=False)


def downgrade() -> None:
    # Drop system_metrics table
    op.drop_index(op.f('ix_system_metrics_recorded_at'), table_name='system_metrics')
    op.drop_index(op.f('ix_system_metrics_metric_name'), table_name='system_metrics')
    op.drop_index(op.f('ix_system_metrics_id'), table_name='system_metrics')
    op.drop_table('system_metrics')

    # Drop admin_logs table
    op.drop_index(op.f('ix_admin_logs_resource_type'), table_name='admin_logs')
    op.drop_index(op.f('ix_admin_logs_level'), table_name='admin_logs')
    op.drop_index(op.f('ix_admin_logs_id'), table_name='admin_logs')
    op.drop_index(op.f('ix_admin_logs_created_at'), table_name='admin_logs')
    op.drop_index(op.f('ix_admin_logs_action'), table_name='admin_logs')
    op.drop_table('admin_logs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS actiontype')
    op.execute('DROP TYPE IF EXISTS loglevel')
