from typing import Optional
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from src.config import settings
from src.models.embeddings import EmbeddingModel, get_embedding_model
from src.utils.errors import VectorSearchError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PineconeClient:
    """Pinecone vector database client for semantic search."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
        embedding_model: Optional[EmbeddingModel] = None,
    ):
        self.api_key = api_key or settings.pinecone_api_key
        self.index_name = index_name or settings.pinecone_index_name
        self.embedding_model = embedding_model or get_embedding_model()
        self._client: Optional[Pinecone] = None
        self._index = None

    def _get_client(self) -> Pinecone:
        """Get or create Pinecone client."""
        if not self.api_key:
            raise VectorSearchError("Pinecone API key not configured")

        if self._client is None:
            self._client = Pinecone(api_key=self.api_key)
            logger.info("Pinecone client initialized")

        return self._client

    def _get_index(self):
        """Get or create Pinecone index."""
        if self._index is None:
            client = self._get_client()
            self._index = client.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")

        return self._index

    def create_index(self, dimension: int = settings.embedding_dimension) -> None:
        """Create the Pinecone index if it doesn't exist."""
        client = self._get_client()

        existing_indexes = [idx.name for idx in client.list_indexes()]

        if self.index_name in existing_indexes:
            logger.info(f"Index '{self.index_name}' already exists")
            return

        client.create_index(
            name=self.index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info(f"Created Pinecone index: {self.index_name}")

    async def upsert(
        self,
        id: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Upsert a vector with text embedding.

        Args:
            id: Unique identifier for the vector
            text: Text to embed and store
            metadata: Optional metadata to store with the vector
        """
        try:
            embedding = await self.embedding_model.embed(text)
            index = self._get_index()

            index.upsert(
                vectors=[
                    {
                        "id": id,
                        "values": embedding,
                        "metadata": metadata or {},
                    }
                ]
            )
            logger.debug(f"Upserted vector: {id}")

        except Exception as e:
            raise VectorSearchError(f"Failed to upsert vector: {e}")

    async def upsert_batch(
        self,
        items: list[tuple[str, str, dict]],
        batch_size: int = 100,
    ) -> None:
        """Upsert multiple vectors in batches.

        Args:
            items: List of (id, text, metadata) tuples
            batch_size: Number of items per batch
        """
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                texts = [item[1] for item in batch]
                embeddings = await self.embedding_model.embed_batch(texts)

                vectors = [
                    {
                        "id": item[0],
                        "values": embedding,
                        "metadata": item[2],
                    }
                    for item, embedding in zip(batch, embeddings)
                ]

                index = self._get_index()
                index.upsert(vectors=vectors)
                logger.debug(f"Upserted batch of {len(vectors)} vectors")

        except Exception as e:
            raise VectorSearchError(f"Failed to upsert batch: {e}")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[dict]:
        """Search for similar vectors.

        Args:
            query: Search query text
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of matches with id, score, and metadata
        """
        try:
            embedding = await self.embedding_model.embed(query)
            index = self._get_index()

            results = index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter,
            )

            matches = [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                }
                for match in results.matches
            ]

            logger.debug(f"Found {len(matches)} matches for query")
            return matches

        except Exception as e:
            raise VectorSearchError(f"Search failed: {e}")

    def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID."""
        try:
            index = self._get_index()
            index.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} vectors")
        except Exception as e:
            raise VectorSearchError(f"Failed to delete vectors: {e}")

    def get_stats(self) -> dict:
        """Get index statistics."""
        try:
            index = self._get_index()
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
            }
        except Exception as e:
            raise VectorSearchError(f"Failed to get stats: {e}")


@lru_cache
def get_pinecone_client() -> PineconeClient:
    """Get singleton Pinecone client instance."""
    return PineconeClient()

