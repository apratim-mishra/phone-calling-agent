from typing import Optional, Annotated

from langchain_core.tools import tool

from src.database.pinecone_client import get_pinecone_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


@tool
async def property_search(
    query: Annotated[str, "Natural language description of desired property"],
    max_price: Annotated[Optional[float], "Maximum price budget"] = None,
    min_bedrooms: Annotated[Optional[int], "Minimum number of bedrooms"] = None,
    city: Annotated[Optional[str], "Preferred city"] = None,
) -> str:
    """Search for properties matching the caller's criteria.

    Use this when the caller describes what kind of property they're looking for.
    Returns a summary of matching properties.
    """
    try:
        pinecone = get_pinecone_client()

        filter_dict = {}
        if max_price:
            filter_dict["price"] = {"$lte": max_price}
        if min_bedrooms:
            filter_dict["bedrooms"] = {"$gte": min_bedrooms}
        if city:
            filter_dict["city"] = {"$eq": city}

        results = await pinecone.search(
            query=query,
            top_k=3,
            filter=filter_dict if filter_dict else None,
        )

        if not results:
            return "No properties found matching those criteria."

        summaries = []
        for i, match in enumerate(results, 1):
            meta = match.get("metadata", {})
            summary = (
                f"{i}. {meta.get('title', 'Property')} - "
                f"${meta.get('price', 0):,.0f}, "
                f"{meta.get('bedrooms', 0)} bed, {meta.get('bathrooms', 0)} bath, "
                f"{meta.get('city', 'Unknown')}, {meta.get('state', '')}"
            )
            summaries.append(summary)

        return "Found properties:\n" + "\n".join(summaries)

    except Exception as e:
        logger.error(f"Property search failed: {e}")
        return "I'm having trouble searching right now. Let me try again or transfer you to an agent."


@tool
def transfer_call(
    reason: Annotated[str, "Reason for transferring the call"],
) -> str:
    """Transfer the call to a human agent.

    Use this when:
    - The caller explicitly asks to speak with a human
    - You cannot adequately help with their request
    - The caller seems frustrated
    """
    logger.info(f"Call transfer requested: {reason}")
    return f"TRANSFER_REQUESTED: {reason}"


@tool
def end_call(
    summary: Annotated[str, "Brief summary of the call"],
) -> str:
    """End the call politely.

    Use this when:
    - The caller indicates they're done
    - The conversation has naturally concluded
    - The caller says goodbye
    """
    logger.info(f"Call ending: {summary}")
    return f"CALL_ENDED: {summary}"


AVAILABLE_TOOLS = [property_search, transfer_call, end_call]

