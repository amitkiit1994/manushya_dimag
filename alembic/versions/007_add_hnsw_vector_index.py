"""Add HNSW vector index for enterprise-scale search

Revision ID: 007_add_hnsw_vector_index
Revises: 009aabbccd
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_hnsw_vector_index'
down_revision = '009aabbccd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add HNSW vector index for enterprise-scale vector search"""
    
    # Create HNSW index for vector similarity search
    # Note: For production deployment with large datasets, consider:
    # 1. Run this migration during low-traffic hours
    # 2. For zero-downtime deployments, create index CONCURRENTLY in a separate step
    # 3. Monitor index creation progress with: SELECT * FROM pg_stat_progress_create_index;
    op.execute("""
        CREATE INDEX idx_memories_vector_hnsw 
        ON memories USING hnsw (vector vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64);
    """)
    
    # Create additional indexes for hybrid search performance
    op.execute("""
        CREATE INDEX idx_memories_tenant_type_created 
        ON memories (tenant_id, type, created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_memories_tenant_ttl 
        ON memories (tenant_id, ttl_days) 
        WHERE ttl_days IS NOT NULL;
    """)


def downgrade() -> None:
    """Remove HNSW vector index"""
    op.execute("DROP INDEX IF EXISTS idx_memories_vector_hnsw;")
    op.execute("DROP INDEX IF EXISTS idx_memories_tenant_type_created;")
    op.execute("DROP INDEX IF EXISTS idx_memories_tenant_ttl;") 