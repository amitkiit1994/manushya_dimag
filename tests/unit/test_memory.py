"""
Unit tests for memory system
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from manushya.db.models import Memory, Identity
from manushya.services.embedding_service import generate_embedding
from manushya.services.memory_service import MemoryService
from manushya.core.exceptions import NotFoundError, ValidationError


class TestMemoryService:
    """Test memory service functionality."""

    @pytest.fixture
    def memory_service(self, db_session):
        """Create memory service instance."""
        return MemoryService(db_session)

    @pytest.mark.asyncio
    async def test_create_memory_success(self, memory_service, identity, test_memory):
        """Test successful memory creation."""
        memory_data = test_memory.copy()
        
        # Mock embedding generation
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=memory_data["text"],
                memory_type=memory_data["type"],
                metadata=memory_data["metadata"],
                ttl_days=memory_data["ttl_days"],
                tenant_id=identity.tenant_id
            )
            
            assert memory.text == memory_data["text"]
            assert memory.type == memory_data["type"]
            assert memory.meta_data == memory_data["metadata"]
            assert memory.identity_id == identity.id
            assert memory.vector is not None
            assert len(memory.vector) == 1536

    @pytest.mark.asyncio
    async def test_create_memory_without_embedding(self, memory_service, identity, test_memory):
        """Test memory creation without embedding."""
        memory_data = test_memory.copy()
        
        memory = await memory_service.create_memory(
            identity_id=identity.id,
            text=memory_data["text"],
            memory_type=memory_data["type"],
            metadata=memory_data["metadata"],
            ttl_days=memory_data["ttl_days"],
            tenant_id=identity.tenant_id,
            generate_embedding=False
        )
        
        assert memory.text == memory_data["text"]
        assert memory.vector is None

    @pytest.mark.asyncio
    async def test_create_memory_embedding_error(self, memory_service, identity, test_memory):
        """Test memory creation with embedding error."""
        memory_data = test_memory.copy()
        
        # Mock embedding generation to fail
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.side_effect = Exception("Embedding service error")
            
            # Should still create memory without embedding
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=memory_data["text"],
                memory_type=memory_data["type"],
                metadata=memory_data["metadata"],
                ttl_days=memory_data["ttl_days"],
                tenant_id=identity.tenant_id
            )
            
            assert memory.text == memory_data["text"]
            assert memory.vector is None

    @pytest.mark.asyncio
    async def test_get_memory_success(self, memory_service, memory):
        """Test successful memory retrieval."""
        retrieved_memory = await memory_service.get_memory(memory.id)
        
        assert retrieved_memory.id == memory.id
        assert retrieved_memory.text == memory.text
        assert retrieved_memory.type == memory.type

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, memory_service):
        """Test memory retrieval with non-existent ID."""
        import uuid
        
        with pytest.raises(NotFoundError):
            await memory_service.get_memory(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_memory_deleted(self, memory_service, memory):
        """Test memory retrieval of deleted memory."""
        # Mark memory as deleted
        memory.is_deleted = True
        memory.deleted_at = datetime.utcnow()
        
        with pytest.raises(NotFoundError):
            await memory_service.get_memory(memory.id)

    @pytest.mark.asyncio
    async def test_list_memories(self, memory_service, identity):
        """Test memory listing."""
        # Create multiple memories
        memories = []
        for i in range(5):
            memory_data = {
                "text": f"Memory {i}",
                "type": "test_memory",
                "metadata": {"index": i},
                "ttl_days": 30
            }
            
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=memory_data["text"],
                memory_type=memory_data["type"],
                metadata=memory_data["metadata"],
                ttl_days=memory_data["ttl_days"],
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            memories.append(memory)
        
        # List memories
        result = await memory_service.list_memories(
            identity_id=identity.id,
            skip=0,
            limit=10
        )
        
        assert len(result) == 5
        assert all(m.identity_id == identity.id for m in result)

    @pytest.mark.asyncio
    async def test_list_memories_with_filters(self, memory_service, identity):
        """Test memory listing with filters."""
        # Create memories with different types
        memory_types = ["meeting_note", "task", "meeting_note", "task"]
        for i, memory_type in enumerate(memory_types):
            await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Memory {i}",
                memory_type=memory_type,
                metadata={"index": i},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
        
        # Filter by type
        meeting_notes = await memory_service.list_memories(
            identity_id=identity.id,
            memory_type="meeting_note"
        )
        assert len(meeting_notes) == 2
        
        tasks = await memory_service.list_memories(
            identity_id=identity.id,
            memory_type="task"
        )
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_update_memory_success(self, memory_service, memory):
        """Test successful memory update."""
        update_data = {
            "text": "Updated memory text",
            "metadata": {"updated": True, "timestamp": datetime.utcnow().isoformat()}
        }
        
        updated_memory = await memory_service.update_memory(
            memory.id,
            text=update_data["text"],
            metadata=update_data["metadata"]
        )
        
        assert updated_memory.text == update_data["text"]
        assert updated_memory.meta_data == update_data["metadata"]
        assert updated_memory.version == memory.version + 1

    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, memory_service):
        """Test memory update with non-existent ID."""
        import uuid
        
        with pytest.raises(NotFoundError):
            await memory_service.update_memory(
                uuid.uuid4(),
                text="Updated text"
            )

    @pytest.mark.asyncio
    async def test_delete_memory_soft(self, memory_service, memory):
        """Test soft memory deletion."""
        await memory_service.delete_memory(memory.id, hard_delete=False)
        
        # Memory should be marked as deleted but not removed
        assert memory.is_deleted is True
        assert memory.deleted_at is not None

    @pytest.mark.asyncio
    async def test_delete_memory_hard(self, memory_service, memory):
        """Test hard memory deletion."""
        memory_id = memory.id
        await memory_service.delete_memory(memory_id, hard_delete=True)
        
        # Memory should be completely removed
        with pytest.raises(NotFoundError):
            await memory_service.get_memory(memory_id)

    @pytest.mark.asyncio
    async def test_bulk_delete_memories(self, memory_service, identity):
        """Test bulk memory deletion."""
        # Create multiple memories
        memories = []
        for i in range(5):
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Memory {i}",
                memory_type="test_memory",
                metadata={"index": i},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            memories.append(memory)
        
        memory_ids = [m.id for m in memories[:3]]
        
        result = await memory_service.bulk_delete_memories(
            memory_ids=memory_ids,
            hard_delete=False
        )
        
        assert result["deleted_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["failed_memories"]) == 0

    @pytest.mark.asyncio
    async def test_bulk_delete_memories_partial_failure(self, memory_service, identity):
        """Test bulk memory deletion with partial failures."""
        # Create memories
        memories = []
        for i in range(3):
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Memory {i}",
                memory_type="test_memory",
                metadata={"index": i},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            memories.append(memory)
        
        # Include one non-existent ID
        import uuid
        memory_ids = [memories[0].id, memories[1].id, uuid.uuid4()]
        
        result = await memory_service.bulk_delete_memories(
            memory_ids=memory_ids,
            hard_delete=False
        )
        
        assert result["deleted_count"] == 2
        assert result["failed_count"] == 1
        assert len(result["failed_memories"]) == 1


class TestVectorSearch:
    """Test vector search functionality."""

    @pytest.mark.asyncio
    async def test_search_memories_similarity(self, memory_service, identity):
        """Test memory search with similarity."""
        # Create memories with embeddings
        memories = []
        for i in range(5):
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Memory about topic {i}",
                memory_type="test_memory",
                metadata={"topic": f"topic_{i}"},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            # Set mock embeddings
            memory.vector = [0.1 + i * 0.1] * 1536
            memories.append(memory)
        
        # Mock embedding generation for search query
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            results = await memory_service.search_memories(
                query="topic",
                identity_id=identity.id,
                limit=10,
                similarity_threshold=0.5
            )
            
            assert len(results) > 0
            assert all(hasattr(m, 'score') for m in results)

    @pytest.mark.asyncio
    async def test_search_memories_no_results(self, memory_service, identity):
        """Test memory search with no results."""
        # Create memory with different embedding
        memory = await memory_service.create_memory(
            identity_id=identity.id,
            text="Memory about different topic",
            memory_type="test_memory",
            metadata={"topic": "different"},
            ttl_days=30,
            tenant_id=identity.tenant_id,
            generate_embedding=False
        )
        memory.vector = [0.9] * 1536  # Very different embedding
        
        # Mock embedding generation for search query
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            results = await memory_service.search_memories(
                query="topic",
                identity_id=identity.id,
                limit=10,
                similarity_threshold=0.8  # High threshold
            )
            
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_memories_with_type_filter(self, memory_service, identity):
        """Test memory search with type filter."""
        # Create memories with different types
        for i in range(3):
            await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Meeting note {i}",
                memory_type="meeting_note",
                metadata={"meeting_id": f"meeting_{i}"},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
        
        for i in range(2):
            await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Task {i}",
                memory_type="task",
                metadata={"task_id": f"task_{i}"},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
        
        # Mock embedding generation
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            # Search with type filter
            meeting_results = await memory_service.search_memories(
                query="meeting",
                identity_id=identity.id,
                memory_type="meeting_note",
                limit=10
            )
            
            task_results = await memory_service.search_memories(
                query="task",
                identity_id=identity.id,
                memory_type="task",
                limit=10
            )
            
            assert len(meeting_results) == 3
            assert len(task_results) == 2

    @pytest.mark.asyncio
    async def test_search_memories_tenant_isolation(self, memory_service, identity):
        """Test memory search respects tenant isolation."""
        # Create memory for current tenant
        memory = await memory_service.create_memory(
            identity_id=identity.id,
            text="Tenant-specific memory",
            memory_type="test_memory",
            metadata={"tenant": "current"},
            ttl_days=30,
            tenant_id=identity.tenant_id,
            generate_embedding=False
        )
        
        # Mock embedding generation
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            # Search should only return memories from current tenant
            results = await memory_service.search_memories(
                query="memory",
                identity_id=identity.id,
                limit=10
            )
            
            assert len(results) == 1
            assert results[0].tenant_id == identity.tenant_id


class TestMemoryValidation:
    """Test memory validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_memory_text_length(self, memory_service, identity):
        """Test memory text length validation."""
        # Test empty text
        with pytest.raises(ValidationError):
            await memory_service.create_memory(
                identity_id=identity.id,
                text="",
                memory_type="test_memory",
                metadata={},
                ttl_days=30,
                tenant_id=identity.tenant_id
            )
        
        # Test very long text
        long_text = "x" * 10001  # Exceeds max length
        with pytest.raises(ValidationError):
            await memory_service.create_memory(
                identity_id=identity.id,
                text=long_text,
                memory_type="test_memory",
                metadata={},
                ttl_days=30,
                tenant_id=identity.tenant_id
            )

    @pytest.mark.asyncio
    async def test_validate_memory_type(self, memory_service, identity):
        """Test memory type validation."""
        # Test invalid memory type
        with pytest.raises(ValidationError):
            await memory_service.create_memory(
                identity_id=identity.id,
                text="Valid text",
                memory_type="",  # Empty type
                metadata={},
                ttl_days=30,
                tenant_id=identity.tenant_id
            )

    @pytest.mark.asyncio
    async def test_validate_memory_metadata(self, memory_service, identity):
        """Test memory metadata validation."""
        # Test metadata size limit
        large_metadata = {"key": "x" * 10000}  # Very large metadata
        
        with pytest.raises(ValidationError):
            await memory_service.create_memory(
                identity_id=identity.id,
                text="Valid text",
                memory_type="test_memory",
                metadata=large_metadata,
                ttl_days=30,
                tenant_id=identity.tenant_id
            )

    @pytest.mark.asyncio
    async def test_validate_memory_ttl(self, memory_service, identity):
        """Test memory TTL validation."""
        # Test negative TTL
        with pytest.raises(ValidationError):
            await memory_service.create_memory(
                identity_id=identity.id,
                text="Valid text",
                memory_type="test_memory",
                metadata={},
                ttl_days=-1,
                tenant_id=identity.tenant_id
            )
        
        # Test very large TTL
        with pytest.raises(ValidationError):
            await memory_service.create_memory(
                identity_id=identity.id,
                text="Valid text",
                memory_type="test_memory",
                metadata={},
                ttl_days=10000,  # Too large
                tenant_id=identity.tenant_id
            )


class TestMemoryPerformance:
    """Performance tests for memory system."""

    @pytest.mark.asyncio
    async def test_bulk_memory_creation(self, memory_service, identity):
        """Test bulk memory creation performance."""
        import time
        
        start_time = time.time()
        
        # Create 100 memories
        memories = []
        for i in range(100):
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Memory {i}",
                memory_type="test_memory",
                metadata={"index": i},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            memories.append(memory)
        
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 10.0
        assert len(memories) == 100

    @pytest.mark.asyncio
    async def test_vector_search_performance(self, memory_service, identity):
        """Test vector search performance."""
        import time
        
        # Create memories with embeddings
        memories = []
        for i in range(50):
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Memory {i}",
                memory_type="test_memory",
                metadata={"index": i},
                ttl_days=30,
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            memory.vector = [0.1 + (i % 10) * 0.1] * 1536
            memories.append(memory)
        
        # Mock embedding generation
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            start_time = time.time()
            results = await memory_service.search_memories(
                query="test query",
                identity_id=identity.id,
                limit=20,
                similarity_threshold=0.5
            )
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 5.0
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_memory_cleanup_performance(self, memory_service, identity):
        """Test memory cleanup performance."""
        import time
        
        # Create expired memories
        expired_memories = []
        for i in range(100):
            memory = await memory_service.create_memory(
                identity_id=identity.id,
                text=f"Expired memory {i}",
                memory_type="test_memory",
                metadata={"index": i},
                ttl_days=1,  # Short TTL
                tenant_id=identity.tenant_id,
                generate_embedding=False
            )
            # Manually set as expired
            memory.created_at = datetime.utcnow() - timedelta(days=2)
            expired_memories.append(memory)
        
        start_time = time.time()
        cleaned_count = await memory_service.cleanup_expired_memories()
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0
        assert cleaned_count > 0


class TestMemoryEdgeCases:
    """Edge case tests for memory system."""

    @pytest.mark.asyncio
    async def test_memory_with_special_characters(self, memory_service, identity):
        """Test memory creation with special characters."""
        special_text = "Memory with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        memory = await memory_service.create_memory(
            identity_id=identity.id,
            text=special_text,
            memory_type="test_memory",
            metadata={"special": True},
            ttl_days=30,
            tenant_id=identity.tenant_id,
            generate_embedding=False
        )
        
        assert memory.text == special_text

    @pytest.mark.asyncio
    async def test_memory_with_unicode(self, memory_service, identity):
        """Test memory creation with unicode text."""
        unicode_text = "Memory with unicode: 测试文本 🚀 émojis"
        
        memory = await memory_service.create_memory(
            identity_id=identity.id,
            text=unicode_text,
            memory_type="test_memory",
            metadata={"unicode": True},
            ttl_days=30,
            tenant_id=identity.tenant_id,
            generate_embedding=False
        )
        
        assert memory.text == unicode_text

    @pytest.mark.asyncio
    async def test_memory_with_large_metadata(self, memory_service, identity):
        """Test memory creation with large metadata."""
        large_metadata = {
            "array": list(range(1000)),
            "nested": {
                "deep": {
                    "structure": {
                        "with": "lots of data"
                    }
                }
            }
        }
        
        memory = await memory_service.create_memory(
            identity_id=identity.id,
            text="Memory with large metadata",
            memory_type="test_memory",
            metadata=large_metadata,
            ttl_days=30,
            tenant_id=identity.tenant_id,
            generate_embedding=False
        )
        
        assert memory.meta_data == large_metadata

    @pytest.mark.asyncio
    async def test_memory_versioning(self, memory_service, memory):
        """Test memory versioning on updates."""
        original_version = memory.version
        
        # Update memory
        updated_memory = await memory_service.update_memory(
            memory.id,
            text="Updated text"
        )
        
        assert updated_memory.version == original_version + 1
        
        # Update again
        updated_memory = await memory_service.update_memory(
            memory.id,
            metadata={"updated": True}
        )
        
        assert updated_memory.version == original_version + 2

    @pytest.mark.asyncio
    async def test_memory_soft_delete_recovery(self, memory_service, memory):
        """Test memory soft delete and recovery."""
        # Soft delete
        await memory_service.delete_memory(memory.id, hard_delete=False)
        
        # Should not be retrievable normally
        with pytest.raises(NotFoundError):
            await memory_service.get_memory(memory.id)
        
        # But should be recoverable with include_deleted flag
        recovered_memory = await memory_service.get_memory(
            memory.id, 
            include_deleted=True
        )
        
        assert recovered_memory.id == memory.id
        assert recovered_memory.is_deleted is True 