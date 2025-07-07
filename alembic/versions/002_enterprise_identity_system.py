"""Enterprise Identity System

Revision ID: 002
Revises: 001
Create Date: 2025-07-05 10:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tenants_name', 'tenants', ['name'])

    # Add tenant_id to existing tables
    op.add_column('identities', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('memories', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('policies', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('audit_logs', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key constraints for tenant_id
    op.create_foreign_key('fk_identities_tenant_id', 'identities', 'tenants', ['tenant_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_memories_tenant_id', 'memories', 'tenants', ['tenant_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_policies_tenant_id', 'policies', 'tenants', ['tenant_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_audit_logs_tenant_id', 'audit_logs', 'tenants', ['tenant_id'], ['id'], ondelete='SET NULL')

    # Create indexes for tenant_id
    op.create_index('idx_identities_tenant_id', 'identities', ['tenant_id'])
    op.create_index('idx_memories_tenant_id', 'memories', ['tenant_id'])
    op.create_index('idx_policies_tenant_id', 'policies', ['tenant_id'])
    op.create_index('idx_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('token_hash', sa.Text(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_api_keys_token_hash', 'api_keys', ['token_hash'])
    op.create_index('idx_api_keys_tenant_id', 'api_keys', ['tenant_id'])
    op.create_index('idx_api_keys_identity_id', 'api_keys', ['identity_id'])
    op.create_index('idx_api_keys_expires_at', 'api_keys', ['expires_at'])

    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessions_identity_id', 'sessions', ['identity_id'])
    op.create_index('idx_sessions_expires_at', 'sessions', ['expires_at'])
    op.create_index('idx_sessions_revoked_at', 'sessions', ['revoked_at'])

    # Create identity_invites table
    op.create_table('identity_invites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_identity_invites_email', 'identity_invites', ['email'])
    op.create_index('idx_identity_invites_token', 'identity_invites', ['token'])
    op.create_index('idx_identity_invites_tenant_id', 'identity_invites', ['tenant_id'])
    op.create_index('idx_identity_invites_expires_at', 'identity_invites', ['expires_at'])

    # Create external_identities table
    op.create_table('external_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('external_id', sa.Text(), nullable=False),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'external_id', name='uq_external_identities_provider_external_id')
    )
    op.create_index('idx_external_identities_provider', 'external_identities', ['provider'])
    op.create_index('idx_external_identities_identity_id', 'external_identities', ['identity_id'])

    # Add refresh_token to sessions table
    op.add_column('sessions', sa.Column('refresh_token', sa.Text(), nullable=False))
    op.create_index('idx_sessions_refresh_token', 'sessions', ['refresh_token'])


def downgrade() -> None:
    # Drop external_identities table
    op.drop_table('external_identities')

    # Drop identity_invites table
    op.drop_table('identity_invites')

    # Drop sessions table
    op.drop_table('sessions')

    # Drop api_keys table
    op.drop_table('api_keys')

    # Remove tenant_id columns and constraints
    op.drop_constraint('fk_audit_logs_tenant_id', 'audit_logs', type_='foreignkey')
    op.drop_constraint('fk_policies_tenant_id', 'policies', type_='foreignkey')
    op.drop_constraint('fk_memories_tenant_id', 'memories', type_='foreignkey')
    op.drop_constraint('fk_identities_tenant_id', 'identities', type_='foreignkey')

    op.drop_index('idx_audit_logs_tenant_id', 'audit_logs')
    op.drop_index('idx_policies_tenant_id', 'policies')
    op.drop_index('idx_memories_tenant_id', 'memories')
    op.drop_index('idx_identities_tenant_id', 'identities')

    op.drop_column('audit_logs', 'tenant_id')
    op.drop_column('policies', 'tenant_id')
    op.drop_column('memories', 'tenant_id')
    op.drop_column('identities', 'tenant_id')

    # Drop tenants table
    op.drop_table('tenants')
