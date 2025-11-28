from typing import Optional
from functools import lru_cache

import httpx
import numpy as np

from src.config import settings
from src.utils.errors import VectorSearchError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """OpenAI embeddings for vector search."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.api_key:
            raise VectorSearchError("OpenAI API key required for embeddings")

        try:
            client = await self._get_client()
            response = await client.post(
                "/embeddings",
                json={
                    "input": texts,
                    "model": self.model,
                },
            )
            response.raise_for_status()
            data = response.json()

            embeddings = [item["embedding"] for item in data["data"]]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except httpx.HTTPError as e:
            raise VectorSearchError(f"Embedding API request failed: {e}")
        except Exception as e:
            raise VectorSearchError(f"Failed to generate embeddings: {e}")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    """Get singleton embedding model instance."""
    return EmbeddingModel()

