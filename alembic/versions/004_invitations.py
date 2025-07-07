"""Add Invitations

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create invitations table
    op.create_table('invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('claims', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_accepted', sa.Boolean(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['identities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_invitations_email_tenant', 'invitations', ['email', 'tenant_id'])
    op.create_index('idx_invitations_token', 'invitations', ['token'])
    op.create_index('idx_invitations_expires_at', 'invitations', ['expires_at'])
    op.create_index('idx_invitations_accepted', 'invitations', ['is_accepted'])
    op.create_index('ix_invitations_token', 'invitations', ['token'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_invitations_token', table_name='invitations')
    op.drop_index('idx_invitations_accepted', table_name='invitations')
    op.drop_index('idx_invitations_expires_at', table_name='invitations')
    op.drop_index('idx_invitations_token', table_name='invitations')
    op.drop_index('idx_invitations_email_tenant', table_name='invitations')

    # Drop table
    op.drop_table('invitations')
