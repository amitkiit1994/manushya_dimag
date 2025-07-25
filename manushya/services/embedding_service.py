"""
Embedding service for generating vector embeddings
"""

import asyncio

import httpx
import numpy as np

from manushya.config import settings
from manushya.core.exceptions import EmbeddingError


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.dimension = settings.vector_dimension
        self.model = settings.embedding_model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if not text.strip():
            raise EmbeddingError("Text cannot be empty")
        
        # Try OpenAI first if configured
        if settings.openai_api_key:
            try:
                return await self._call_openai_embedding(text)
            except Exception as e:
                # Log the error but continue with fallback
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"OpenAI embedding failed, using fallback: {str(e)}")
        
        # Fallback to local embedding
        return await self._generate_local_embedding(text)

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        # Process in batches to avoid overwhelming the service
        batch_size = 10
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch]
            )
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    async def _generate_local_embedding(self, text: str) -> list[float]:
        """Generate a local embedding using sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Load model (cached after first load)
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embedding
            embedding = model.encode(text, convert_to_tensor=False)
            
            # Ensure correct dimension (pad or truncate if needed)
            if len(embedding) < self.dimension:
                embedding = np.pad(embedding, (0, self.dimension - len(embedding)))
            elif len(embedding) > self.dimension:
                embedding = embedding[:self.dimension]
            
            # Normalize the vector
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            
            return embedding_array.tolist()
            
        except ImportError:
            # Fallback to hash-based embedding if sentence-transformers not available
            return await self._generate_hash_embedding(text)
    
    async def _generate_hash_embedding(self, text: str) -> list[float]:
        """Generate a hash-based embedding as fallback."""
        import hashlib
        
        # Create a hash of the text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        # Convert hash to a list of floats
        embedding = []
        for i in range(0, len(text_hash), 2):
            if len(embedding) >= self.dimension:
                break
            hex_pair = text_hash[i : i + 2]
            float_val = int(hex_pair, 16) / 255.0  # Normalize to [0, 1]
            embedding.append(float_val)
        # Pad or truncate to required dimension
        while len(embedding) < self.dimension:
            embedding.append(0.0)
        embedding = embedding[: self.dimension]
        # Normalize the vector
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
        return embedding_array.tolist()

    async def _call_openai_embedding(self, text: str) -> list[float]:
        """Call OpenAI embedding API."""
        if not settings.embedding_service_api_key:
            raise EmbeddingError("OpenAI API key not configured")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.embedding_service_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": text, "model": self.model},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    raise EmbeddingError(f"OpenAI API error: {response.status_code}")
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            raise EmbeddingError(f"Failed to call OpenAI API: {str(e)}") from e

    async def _call_cohere_embedding(self, text: str) -> list[float]:
        """Call Cohere embedding API."""
        if not settings.embedding_service_api_key:
            raise EmbeddingError("Cohere API key not configured")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/embed",
                    headers={
                        "Authorization": f"Bearer {settings.embedding_service_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"texts": [text], "model": self.model},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    raise EmbeddingError(f"Cohere API error: {response.status_code}")
                data = response.json()
                return data["embeddings"][0]
        except Exception as e:
            raise EmbeddingError(f"Failed to call Cohere API: {str(e)}") from e


# Global embedding service instance
embedding_service = EmbeddingService()


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using the global service."""
    return await embedding_service.generate_embedding(text)


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts using the global service."""
    return await embedding_service.generate_embeddings(texts)
