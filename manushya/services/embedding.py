"""
Production-grade embedding service with OpenAI and local fallback.
"""

import asyncio
import logging
from typing import Any

import numpy as np
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from manushya.config import settings
from manushya.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Production-grade embedding service with OpenAI and local fallback."""

    def __init__(self):
        self.openai_client = None
        self.local_model = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize OpenAI and local embedding clients."""
        # Initialize OpenAI client if API key is available
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI embedding client initialized")
        # Initialize local model as fallback
        try:
            self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Local embedding model initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize local model: {e}")

    async def get_embeddings(
        self, texts: list[str], model: str = "openai"
    ) -> list[list[float]]:
        """
        Get embeddings for a list of texts.
        Args:
            texts: List of texts to embed
            model: Model to use ('openai' or 'local')
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        try:
            if model == "openai" and self.openai_client:
                return await self._get_openai_embeddings(texts)
            elif self.local_model:
                return await self._get_local_embeddings(texts)
            else:
                raise EmbeddingError("No embedding model available")
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(f"Failed to generate embeddings: {str(e)}") from e

    async def _get_openai_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings using OpenAI API."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002", input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}")
            # Fallback to local model
            if self.local_model:
                logger.info("Falling back to local embedding model")
                return await self._get_local_embeddings(texts)
            else:
                raise EmbeddingError(f"OpenAI embedding failed: {str(e)}") from e

    async def _get_local_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings using local SentenceTransformer model."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.local_model.encode, texts
            )
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Local embedding failed: {str(e)}") from e

    async def get_single_embedding(
        self, text: str, model: str = "openai"
    ) -> list[float]:
        """
        Get embedding for a single text.
        Args:
            text: Text to embed
            model: Model to use ('openai' or 'local')
        Returns:
            Embedding vector
        """
        embeddings = await self.get_embeddings([text], model)
        return embeddings[0] if embeddings else []

    def calculate_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        Returns:
            Similarity score between 0 and 1
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            # Normalize vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            # Calculate cosine similarity
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0

    async def batch_embed_texts(
        self, texts: list[str], batch_size: int = 100, model: str = "openai"
    ) -> list[list[float]]:
        """
        Get embeddings for texts in batches.
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per batch
            model: Model to use ('openai' or 'local')
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self.get_embeddings(batch, model)
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    def get_model_info(self) -> dict[str, Any]:
        """Get information about available embedding models."""
        return {
            "openai_available": self.openai_client is not None,
            "local_available": self.local_model is not None,
            "openai_model": "text-embedding-ada-002" if self.openai_client else None,
            "local_model": "all-MiniLM-L6-v2" if self.local_model else None,
        }


# Global instance
embedding_service = EmbeddingService()
