from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.database.models import Property
from src.database.pinecone_client import PineconeClient, get_pinecone_client
from src.utils.errors import VectorSearchError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Semantic search service for properties."""

    def __init__(self, pinecone_client: Optional[PineconeClient] = None):
        self.pinecone = pinecone_client or get_pinecone_client()

    async def search_properties(
        self,
        query: str,
        max_price: Optional[float] = None,
        min_bedrooms: Optional[int] = None,
        city: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """Search for properties using semantic search.

        Args:
            query: Natural language search query
            max_price: Maximum price filter
            min_bedrooms: Minimum bedrooms filter
            city: City filter
            limit: Maximum results to return

        Returns:
            List of matching properties with scores
        """
        try:
            filter_dict = {}
            if max_price:
                filter_dict["price"] = {"$lte": max_price}
            if min_bedrooms:
                filter_dict["bedrooms"] = {"$gte": min_bedrooms}
            if city:
                filter_dict["city"] = {"$eq": city}

            results = await self.pinecone.search(
                query=query,
                top_k=limit,
                filter=filter_dict if filter_dict else None,
            )

            properties = []
            for match in results:
                property_data = {
                    "id": match["id"],
                    "score": match["score"],
                    **match.get("metadata", {}),
                }
                properties.append(property_data)

            logger.info(f"Found {len(properties)} properties for query: {query[:50]}...")
            return properties

        except Exception as e:
            raise VectorSearchError(f"Property search failed: {e}")

    async def get_property_by_id(self, property_id: int) -> Optional[dict]:
        """Get a property by ID from the database.

        Args:
            property_id: Property ID

        Returns:
            Property dictionary or None
        """
        async with async_session_maker() as session:
            result = await session.execute(
                select(Property).where(Property.id == property_id)
            )
            property_obj = result.scalar_one_or_none()

            if property_obj:
                return property_obj.to_dict()

            return None

    async def index_property(self, property_obj: Property) -> None:
        """Index a property in Pinecone.

        Args:
            property_obj: Property to index
        """
        try:
            search_text = property_obj.to_search_text()
            metadata = {
                "title": property_obj.title,
                "price": property_obj.price,
                "bedrooms": property_obj.bedrooms,
                "bathrooms": property_obj.bathrooms,
                "square_feet": property_obj.square_feet,
                "city": property_obj.city,
                "state": property_obj.state,
                "address": property_obj.address,
            }

            await self.pinecone.upsert(
                id=str(property_obj.id),
                text=search_text,
                metadata=metadata,
            )

            logger.info(f"Indexed property: {property_obj.id}")

        except Exception as e:
            raise VectorSearchError(f"Failed to index property: {e}")

    async def index_all_properties(self, batch_size: int = 100) -> int:
        """Index all properties from the database.

        Args:
            batch_size: Number of properties per batch

        Returns:
            Number of properties indexed
        """
        async with async_session_maker() as session:
            result = await session.execute(select(Property))
            properties = result.scalars().all()

            if not properties:
                logger.warning("No properties found to index")
                return 0

            items = []
            for prop in properties:
                items.append(
                    (
                        str(prop.id),
                        prop.to_search_text(),
                        {
                            "title": prop.title,
                            "price": prop.price,
                            "bedrooms": prop.bedrooms,
                            "bathrooms": prop.bathrooms,
                            "square_feet": prop.square_feet,
                            "city": prop.city,
                            "state": prop.state,
                            "address": prop.address,
                        },
                    )
                )

            await self.pinecone.upsert_batch(items, batch_size=batch_size)
            logger.info(f"Indexed {len(properties)} properties")
            return len(properties)

    def format_results_for_speech(self, properties: list[dict]) -> str:
        """Format search results for text-to-speech.

        Args:
            properties: List of property dictionaries

        Returns:
            Formatted string for speaking
        """
        if not properties:
            return "I couldn't find any properties matching your criteria."

        count = len(properties)
        result_word = "property" if count == 1 else "properties"

        lines = [f"I found {count} {result_word} that might interest you."]

        for i, prop in enumerate(properties[:3], 1):
            price = prop.get("price", 0)
            beds = prop.get("bedrooms", 0)
            baths = prop.get("bathrooms", 0)
            city = prop.get("city", "")

            lines.append(
                f"Option {i}: A {beds} bedroom, {baths} bathroom home in {city} "
                f"for ${price:,.0f}."
            )

        if count > 3:
            lines.append(f"I have {count - 3} more options if you'd like to hear them.")

        return " ".join(lines)

