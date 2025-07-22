"""Convert memories.vector column to pgvector type

Revision ID: 009aabbccd
Revises: f4b5c097ab35
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '009aabbccd'
down_revision = 'f4b5c097ab35'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Rename old column for backup
    op.alter_column('memories', 'vector', new_column_name='vector_old', existing_type=postgresql.ARRAY(sa.Float))
    # 2. Add new pgvector column
    op.add_column('memories', sa.Column('vector', Vector(384), nullable=True))
    # 3. Migrate data (if any)
    op.execute("""
        UPDATE memories SET vector = vector_old::vector
        WHERE vector_old IS NOT NULL
    """)
    # 4. Drop old column
    op.drop_column('memories', 'vector_old')


def downgrade() -> None:
    # 1. Add back old column
    op.add_column('memories', sa.Column('vector_old', postgresql.ARRAY(sa.Float), nullable=True))
    # 2. Migrate data back (if possible)
    op.execute("""
        UPDATE memories SET vector_old = ARRAY(SELECT unnest(vector))
        WHERE vector IS NOT NULL
    """)
    # 3. Drop new column
    op.drop_column('memories', 'vector')
    # 4. Rename old column back
    op.alter_column('memories', 'vector_old', new_column_name='vector', existing_type=postgresql.ARRAY(sa.Float)) 