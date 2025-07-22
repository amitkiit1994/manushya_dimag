#!/usr/bin/env python3
"""
Production HNSW Index Deployment Script

This script handles zero-downtime deployment of HNSW vector indexes
for production environments with large datasets.

Usage:
    python scripts/production_index_deployment.py --action create
    python scripts/production_index_deployment.py --action drop
    python scripts/production_index_deployment.py --action monitor
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from manushya.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionIndexDeployment:
    """Handles production deployment of HNSW indexes with zero downtime."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url)
    
    async def create_index_concurrently(self) -> bool:
        """Create HNSW index with CONCURRENTLY for zero downtime."""
        try:
            async with self.engine.begin() as conn:
                # Check if index already exists
                result = await conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE indexname = 'idx_memories_vector_hnsw'
                """))
                if result.fetchone():
                    logger.warning("Index idx_memories_vector_hnsw already exists")
                    return True
                
                # Create index CONCURRENTLY
                logger.info("Creating HNSW index CONCURRENTLY...")
                await conn.execute(text("""
                    CREATE INDEX CONCURRENTLY idx_memories_vector_hnsw 
                    ON memories USING hnsw (vector) 
                    WITH (m = 16, ef_construction = 64, ef = 40);
                """))
                
                logger.info("✅ HNSW index created successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create HNSW index: {e}")
            return False
    
    async def drop_index(self) -> bool:
        """Drop the HNSW index."""
        try:
            async with self.engine.begin() as conn:
                logger.info("Dropping HNSW index...")
                await conn.execute(text("""
                    DROP INDEX IF EXISTS idx_memories_vector_hnsw;
                """))
                
                logger.info("✅ HNSW index dropped successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to drop HNSW index: {e}")
            return False
    
    async def monitor_index_creation(self) -> None:
        """Monitor index creation progress."""
        try:
            async with self.engine.begin() as conn:
                # Check if index exists
                result = await conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE indexname = 'idx_memories_vector_hnsw'
                """))
                
                if result.fetchone():
                    logger.info("✅ HNSW index exists")
                    
                    # Get index statistics
                    stats = await conn.execute(text("""
                        SELECT 
                            schemaname,
                            tablename,
                            indexname,
                            indexdef
                        FROM pg_indexes 
                        WHERE indexname = 'idx_memories_vector_hnsw'
                    """))
                    
                    for row in stats.fetchall():
                        logger.info(f"Index: {row.indexname}")
                        logger.info(f"Table: {row.schemaname}.{row.tablename}")
                        logger.info(f"Definition: {row.indexdef}")
                else:
                    logger.info("❌ HNSW index does not exist")
                    
                    # Check if there are any ongoing index creations
                    progress = await conn.execute(text("""
                        SELECT * FROM pg_stat_progress_create_index 
                        WHERE index_relname LIKE '%hnsw%'
                    """))
                    
                    ongoing = progress.fetchall()
                    if ongoing:
                        logger.info(f"🔄 Found {len(ongoing)} ongoing index creation(s)")
                        for row in ongoing:
                            logger.info(f"  - {row.index_relname}: {row.command} ({row.phase})")
                    else:
                        logger.info("ℹ️  No ongoing index creation found")
                        
        except Exception as e:
            logger.error(f"❌ Failed to monitor index: {e}")
    
    async def get_table_stats(self) -> None:
        """Get table statistics for capacity planning."""
        try:
            async with self.engine.begin() as conn:
                stats = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE tablename = 'memories' 
                    AND attname = 'vector'
                """))
                
                logger.info("📊 Table Statistics:")
                for row in stats.fetchall():
                    logger.info(f"  - Column: {row.attname}")
                    logger.info(f"  - Distinct values: {row.n_distinct}")
                    logger.info(f"  - Correlation: {row.correlation}")
                    
                # Get table size
                size = await conn.execute(text("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('memories')) as total_size,
                        pg_size_pretty(pg_relation_size('memories')) as table_size,
                        pg_size_pretty(pg_relation_size('memories', 'vm')) as vm_size,
                        pg_size_pretty(pg_relation_size('memories', 'fsm')) as fsm_size
                    FROM pg_class 
                    WHERE relname = 'memories'
                """))
                
                for row in size.fetchall():
                    logger.info(f"  - Total size: {row.total_size}")
                    logger.info(f"  - Table size: {row.table_size}")
                    logger.info(f"  - VM size: {row.vm_size}")
                    logger.info(f"  - FSM size: {row.fsm_size}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to get table stats: {e}")
    
    async def close(self):
        """Close database connection."""
        await self.engine.dispose()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Production HNSW Index Deployment")
    parser.add_argument(
        "--action", 
        choices=["create", "drop", "monitor", "stats"], 
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="Database URL (defaults to settings.database_url)"
    )
    
    args = parser.parse_args()
    
    # Initialize deployment
    deployment = ProductionIndexDeployment(args.database_url)
    
    try:
        if args.action == "create":
            success = await deployment.create_index_concurrently()
            sys.exit(0 if success else 1)
            
        elif args.action == "drop":
            success = await deployment.drop_index()
            sys.exit(0 if success else 1)
            
        elif args.action == "monitor":
            await deployment.monitor_index_creation()
            
        elif args.action == "stats":
            await deployment.get_table_stats()
            
    finally:
        await deployment.close()


if __name__ == "__main__":
    asyncio.run(main()) 