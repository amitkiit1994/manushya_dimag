"""
Unit tests for embedding service
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import numpy as np

from manushya.services.embedding_service import EmbeddingService, generate_embedding, generate_embeddings
from manushya.core.exceptions import EmbeddingError


class TestEmbeddingService:
    """Test embedding service functionality."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        return EmbeddingService()

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service, mock_openai_response):
        """Test successful embedding generation with OpenAI."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openai_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await embedding_service._call_openai_embedding("test text")
            
            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)
            assert all(0 <= x <= 1 for x in result)

    @pytest.mark.asyncio
    async def test_generate_embedding_openai_error(self, embedding_service):
        """Test OpenAI API error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(EmbeddingError, match="OpenAI API error: 401"):
                await embedding_service._call_openai_embedding("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_network_error(self, embedding_service):
        """Test network error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(EmbeddingError, match="Failed to call OpenAI API"):
                await embedding_service._call_openai_embedding("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_timeout(self, embedding_service):
        """Test timeout handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
            
            with pytest.raises(EmbeddingError, match="Failed to call OpenAI API"):
                await embedding_service._call_openai_embedding("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service):
        """Test empty text validation."""
        with pytest.raises(EmbeddingError, match="Text cannot be empty"):
            await embedding_service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_generate_embedding_whitespace_text(self, embedding_service):
        """Test whitespace text validation."""
        with pytest.raises(EmbeddingError, match="Text cannot be empty"):
            await embedding_service.generate_embedding("   ")

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service, mock_openai_response):
        """Test batch embedding generation."""
        texts = ["text1", "text2", "text3"]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openai_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            results = await embedding_service.generate_embeddings(texts)
            
            assert len(results) == 3
            assert all(len(embedding) == 1536 for embedding in results)

    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_list(self, embedding_service):
        """Test empty list handling."""
        results = await embedding_service.generate_embeddings([])
        assert results == []

    @pytest.mark.asyncio
    async def test_generate_embeddings_large_batch(self, embedding_service, mock_openai_response):
        """Test large batch processing."""
        texts = [f"text{i}" for i in range(25)]  # Larger than batch_size=10
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openai_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            results = await embedding_service.generate_embeddings(texts)
            
            assert len(results) == 25
            assert all(len(embedding) == 1536 for embedding in results)

    @pytest.mark.asyncio
    async def test_local_embedding_generation(self, embedding_service):
        """Test local embedding generation using sentence-transformers."""
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = np.array([0.1] * 384)  # all-MiniLM-L6-v2 dimension
            
            result = await embedding_service._generate_local_embedding("test text")
            
            assert len(result) == embedding_service.dimension
            assert all(isinstance(x, float) for x in result)
            # Check normalization
            norm = np.linalg.norm(np.array(result))
            assert abs(norm - 1.0) < 1e-6  # Should be normalized

    @pytest.mark.asyncio
    async def test_local_embedding_consistency(self, embedding_service):
        """Test that same text produces same embedding."""
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = np.array([0.1] * 384)
            
            text = "consistent test text"
            result1 = await embedding_service._generate_local_embedding(text)
            result2 = await embedding_service._generate_local_embedding(text)
            
            assert result1 == result2

    @pytest.mark.asyncio
    async def test_local_embedding_different_texts(self, embedding_service):
        """Test that different texts produce different embeddings."""
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = np.array([0.1] * 384)
            
            result1 = await embedding_service._generate_local_embedding("text1")
            result2 = await embedding_service._generate_local_embedding("text2")
            
            assert result1 != result2

    @pytest.mark.asyncio
    async def test_hash_embedding_fallback(self, embedding_service):
        """Test hash-based embedding fallback when sentence-transformers not available."""
        with patch('sentence_transformers.SentenceTransformer', side_effect=ImportError):
            result = await embedding_service._generate_local_embedding("test text")
            
            assert len(result) == embedding_service.dimension
            assert all(isinstance(x, float) for x in result)
            # Check normalization
            norm = np.linalg.norm(np.array(result))
            assert abs(norm - 1.0) < 1e-6  # Should be normalized

    @pytest.mark.asyncio
    async def test_cohere_embedding_success(self, embedding_service):
        """Test successful Cohere embedding generation."""
        mock_response_data = {
            "embeddings": [[0.1] * 1536],
            "id": "test-id",
            "usage": {"total_tokens": 5}
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await embedding_service._call_cohere_embedding("test text")
            
            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_cohere_embedding_error(self, embedding_service):
        """Test Cohere API error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(EmbeddingError, match="Cohere API error: 400"):
                await embedding_service._call_cohere_embedding("test text")


class TestEmbeddingServiceIntegration:
    """Integration tests for embedding service."""

    @pytest.mark.asyncio
    async def test_generate_embedding_function(self, mock_openai_response):
        """Test the global generate_embedding function."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openai_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await generate_embedding("test text")
            
            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_generate_embeddings_function(self, mock_openai_response):
        """Test the global generate_embeddings function."""
        texts = ["text1", "text2"]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openai_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            results = await generate_embeddings(texts)
            
            assert len(results) == 2
            assert all(len(embedding) == 1536 for embedding in results)

    @pytest.mark.asyncio
    async def test_embedding_service_configuration(self):
        """Test embedding service configuration."""
        service = EmbeddingService()
        
        assert service.dimension == 1536  # OpenAI ada-002 default
        assert service.model == "text-embedding-ada-002"

    @pytest.mark.asyncio
    async def test_embedding_service_error_recovery(self):
        """Test error recovery in embedding service."""
        service = EmbeddingService()
        
        # Test with invalid text
        with pytest.raises(EmbeddingError):
            await service.generate_embedding("")
        
        # Test with valid text should still work
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = np.array([0.1] * 384)
            result = await service._generate_local_embedding("valid text")
            assert len(result) == service.dimension

    @pytest.mark.asyncio
    async def test_generate_embedding_openai_fallback(self, embedding_service):
        """Test that OpenAI failure falls back to local embedding."""
        # Mock OpenAI to fail
        with patch.object(embedding_service, '_call_openai_embedding', side_effect=Exception("OpenAI failed")):
            # Mock local embedding to succeed
            with patch.object(embedding_service, '_generate_local_embedding', return_value=[0.1] * 1536):
                result = await embedding_service.generate_embedding("test text")
                assert len(result) == 1536
                assert all(x == 0.1 for x in result)

    @pytest.mark.asyncio
    async def test_generate_embedding_no_openai_key(self, embedding_service):
        """Test embedding generation when OpenAI key is not configured."""
        # Mock settings to have no OpenAI key
        with patch('manushya.services.embedding_service.settings') as mock_settings:
            mock_settings.openai_api_key = None
            with patch.object(embedding_service, '_generate_local_embedding', return_value=[0.1] * 1536):
                result = await embedding_service.generate_embedding("test text")
                assert len(result) == 1536
                assert all(x == 0.1 for x in result)


class TestEmbeddingServicePerformance:
    """Performance tests for embedding service."""

    @pytest.mark.asyncio
    async def test_embedding_generation_speed(self, embedding_service):
        """Test embedding generation speed."""
        import time
        
        start_time = time.time()
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = np.array([0.1] * 384)
            result = await embedding_service._generate_local_embedding("test text")
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0
        assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_batch_processing_speed(self, embedding_service):
        """Test batch processing speed."""
        import time
        
        texts = [f"text{i}" for i in range(10)]
        
        start_time = time.time()
        results = await embedding_service.generate_embeddings(texts)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_memory_usage(self, embedding_service):
        """Test memory usage for large batches."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate large batch
        texts = [f"text{i}" for i in range(100)]
        results = await embedding_service.generate_embeddings(texts)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
        assert len(results) == 100


class TestEmbeddingServiceEdgeCases:
    """Edge case tests for embedding service."""

    @pytest.mark.asyncio
    async def test_very_long_text(self, embedding_service):
        """Test embedding generation with very long text."""
        long_text = "test " * 1000
        result = await embedding_service._generate_mock_embedding(long_text)
        
        assert len(result) == embedding_service.dimension
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_special_characters(self, embedding_service):
        """Test embedding generation with special characters."""
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = await embedding_service._generate_mock_embedding(special_text)
        
        assert len(result) == embedding_service.dimension
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_unicode_text(self, embedding_service):
        """Test embedding generation with unicode text."""
        unicode_text = "测试文本 with unicode 🚀"
        result = await embedding_service._generate_mock_embedding(unicode_text)
        
        assert len(result) == embedding_service.dimension
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_numeric_text(self, embedding_service):
        """Test embedding generation with numeric text."""
        numeric_text = "1234567890"
        result = await embedding_service._generate_mock_embedding(numeric_text)
        
        assert len(result) == embedding_service.dimension
        assert all(isinstance(x, float) for x in result) 