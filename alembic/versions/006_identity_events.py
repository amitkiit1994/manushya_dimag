"""Add Identity Events

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create identity_events table
    op.create_table('identity_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_delivered', sa.Boolean(), nullable=False),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['identities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_identity_events_type_created', 'identity_events', ['event_type', 'created_at'])
    op.create_index('idx_identity_events_delivered', 'identity_events', ['is_delivered'])
    op.create_index('idx_identity_events_identity_type', 'identity_events', ['identity_id', 'event_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_identity_events_identity_type', table_name='identity_events')
    op.drop_index('idx_identity_events_delivered', table_name='identity_events')
    op.drop_index('idx_identity_events_type_created', table_name='identity_events')

    # Drop table
    op.drop_table('identity_events')
