"""
Memory-related background tasks for Manushya.ai
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, select, update

from manushya.db.database import AsyncSessionLocal
from manushya.db.models import Memory
from manushya.services.embedding_service import generate_embedding
from manushya.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="manushya.tasks.memory_tasks.create_memory_embedding")
def create_memory_embedding_task(self, memory_id: str):
    """Generate embedding for a memory and update the database."""
    try:
        # Convert string ID to UUID
        memory_uuid = uuid.UUID(memory_id)

        # Get memory from database
        async def get_memory():
            async with AsyncSessionLocal() as session:
                stmt = select(Memory).where(Memory.id == memory_uuid)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()

        # Run async function
        memory = asyncio.run(get_memory())
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
        # Generate embedding
        embedding = asyncio.run(generate_embedding(memory.text))

        # Update memory with embedding
        async def update_memory():
            async with AsyncSessionLocal() as session:
                stmt = (
                    update(Memory)
                    .where(Memory.id == memory_uuid)
                    .values(vector=embedding)
                )
                await session.execute(stmt)
                await session.commit()

        asyncio.run(update_memory())
        # Update task status
        self.update_state(
            state="SUCCESS",
            meta={"memory_id": memory_id, "embedding_dimension": len(embedding)},
        )
        return {
            "memory_id": memory_id,
            "embedding_dimension": len(embedding),
            "status": "success",
        }
    except Exception as e:
        # Update task status with error
        self.update_state(
            state="FAILURE", meta={"memory_id": memory_id, "error": str(e)}
        )
        raise


@celery_app.task(bind=True, name="manushya.tasks.memory_tasks.batch_create_embeddings")
def batch_create_embeddings_task(self, memory_ids: list):
    """Generate embeddings for multiple memories."""
    results = []
    for memory_id in memory_ids:
        try:
            result = create_memory_embedding_task.delay(memory_id)
            results.append(
                {"memory_id": memory_id, "task_id": result.id, "status": "queued"}
            )
        except Exception as e:
            results.append(
                {"memory_id": memory_id, "error": str(e), "status": "failed"}
            )
    return results


@celery_app.task(bind=True, name="manushya.tasks.memory_tasks.cleanup_expired_memories")
def cleanup_expired_memories_task(self):
    """Clean up expired memories."""
    try:

        async def cleanup_memories():
            async with AsyncSessionLocal() as session:
                # Find expired memories
                stmt = select(Memory).where(
                    and_(
                        ~Memory.is_deleted,
                        Memory.ttl_days.is_not(None),
                    )
                )
                result = await session.execute(stmt)
                memories = result.scalars().all()
                # Filter expired memories in Python
                expired_memories = []
                for memory in memories:
                    if (
                        memory.ttl_days
                        and memory.created_at
                        < datetime.utcnow() - timedelta(days=memory.ttl_days)
                    ):
                        expired_memories.append(memory)
                # Soft delete expired memories
                for memory in expired_memories:
                    memory.is_deleted = True
                    memory.deleted_at = datetime.utcnow()
                await session.commit()
                return len(expired_memories)

        deleted_count = asyncio.run(cleanup_memories())
        return {"deleted_count": deleted_count, "status": "success"}
    except Exception:
        raise


@celery_app.task(bind=True, name="manushya.tasks.memory_tasks.reindex_memories")
def reindex_memories_task(self, memory_ids: list | None = None):
    """Reindex memories (regenerate embeddings)."""
    try:

        async def reindex_memories():
            async with AsyncSessionLocal() as session:
                # Build query
                stmt = select(Memory).where(
                    and_(
                        ~Memory.is_deleted,
                        Memory.vector.is_(None),  # Only memories without embeddings
                    )
                )
                if memory_ids:
                    memory_uuids = [uuid.UUID(mid) for mid in memory_ids]
                    stmt = stmt.where(Memory.id.in_(memory_uuids))
                result = await session.execute(stmt)
                memories = result.scalars().all()
                # Generate embeddings for each memory
                for memory in memories:
                    try:
                        embedding = await generate_embedding(memory.text)
                        memory.vector = embedding
                    except Exception as e:
                        # Log error but continue with other memories
                        print(
                            f"Failed to generate embedding for memory {memory.id}: {e}"
                        )
                await session.commit()
                return len(memories)

        reindexed_count = asyncio.run(reindex_memories())
        return {"reindexed_count": reindexed_count, "status": "success"}
    except Exception:
        raise
