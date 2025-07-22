"""Add usage metering for enterprise billing

Revision ID: 008_add_usage_metering
Revises: 007_add_hnsw_vector_index
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_usage_metering'
down_revision = '007_add_hnsw_vector_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add usage metering tables for enterprise billing"""
    
    # Usage events table for granular billing
    op.create_table('usage_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event', sa.String(length=100), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False, default=1),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Daily aggregated usage for billing
    op.create_table('usage_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('event', sa.String(length=100), nullable=False),
        sa.Column('units', sa.BigInteger(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'date', 'event', name='uq_usage_daily_tenant_date_event')
    )
    
    # Create indexes for performance
    op.create_index('idx_usage_events_tenant_created', 'usage_events', ['tenant_id', 'created_at'])
    op.create_index('idx_usage_events_event_created', 'usage_events', ['event', 'created_at'])
    op.create_index('idx_usage_daily_tenant_date', 'usage_daily', ['tenant_id', 'date'])


def downgrade() -> None:
    """Remove usage metering tables"""
    op.drop_index('idx_usage_daily_tenant_date', table_name='usage_daily')
    op.drop_index('idx_usage_events_event_created', table_name='usage_events')
    op.drop_index('idx_usage_events_tenant_created', table_name='usage_events')
    op.drop_table('usage_daily')
    op.drop_table('usage_events') 