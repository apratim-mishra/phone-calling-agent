#!/usr/bin/env python3
"""Seed database with sample property data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.config import settings
from src.database import init_db, async_session_maker
from src.database.models import Property
from src.services.search_service import SearchService
from src.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

SAMPLE_PROPERTIES = [
    {
        "title": "Modern Downtown Condo",
        "description": "Stunning 2-bedroom condo in the heart of downtown with floor-to-ceiling windows, "
        "modern kitchen with stainless steel appliances, and amazing city views. Building amenities include "
        "rooftop pool, fitness center, and 24-hour concierge.",
        "price": 450000,
        "bedrooms": 2,
        "bathrooms": 2,
        "square_feet": 1200,
        "location": "Downtown",
        "address": "123 Main Street, Unit 1502",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
    },
    {
        "title": "Spacious Family Home",
        "description": "Beautiful 4-bedroom family home in quiet suburban neighborhood. Features open "
        "floor plan, updated kitchen with granite counters, large backyard with mature trees, "
        "and attached 2-car garage. Top-rated school district.",
        "price": 650000,
        "bedrooms": 4,
        "bathrooms": 3,
        "square_feet": 2800,
        "location": "Suburbs",
        "address": "456 Oak Lane",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78759",
    },
    {
        "title": "Cozy Starter Home",
        "description": "Perfect starter home with 3 bedrooms and charming character. Recently renovated "
        "bathroom, new roof, and energy-efficient windows. Nice fenced backyard and close to parks.",
        "price": 320000,
        "bedrooms": 3,
        "bathrooms": 1.5,
        "square_feet": 1400,
        "location": "East Side",
        "address": "789 Elm Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78702",
    },
    {
        "title": "Luxury Waterfront Estate",
        "description": "Exquisite 5-bedroom waterfront property with private dock. Gourmet kitchen, "
        "home theater, wine cellar, and infinity pool overlooking the lake. Smart home technology throughout.",
        "price": 2500000,
        "bedrooms": 5,
        "bathrooms": 5.5,
        "square_feet": 6500,
        "location": "Lake Travis",
        "address": "100 Lakeshore Drive",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78734",
    },
    {
        "title": "Hip East Austin Bungalow",
        "description": "Renovated 2-bedroom bungalow in trendy East Austin. Original hardwood floors, "
        "updated kitchen, large covered porch. Walking distance to restaurants and shops.",
        "price": 525000,
        "bedrooms": 2,
        "bathrooms": 1,
        "square_feet": 1100,
        "location": "East Austin",
        "address": "234 Holly Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78702",
    },
    {
        "title": "New Construction Townhome",
        "description": "Brand new 3-bedroom townhome with modern finishes. Open concept living, "
        "quartz countertops, stainless appliances, and private rooftop deck with downtown views.",
        "price": 475000,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "square_feet": 1800,
        "location": "South Austin",
        "address": "567 South Congress Ave, Unit B",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78704",
    },
    {
        "title": "Hill Country Ranch",
        "description": "Stunning 4-bedroom ranch home on 5 acres with Hill Country views. Open floor plan, "
        "chef's kitchen, large master suite, and detached workshop. Perfect for horses.",
        "price": 875000,
        "bedrooms": 4,
        "bathrooms": 3,
        "square_feet": 3200,
        "location": "Hill Country",
        "address": "1000 Ranch Road 12",
        "city": "Dripping Springs",
        "state": "TX",
        "zip_code": "78620",
    },
    {
        "title": "Urban Studio Loft",
        "description": "Industrial chic studio loft in converted warehouse. Exposed brick, concrete floors, "
        "12-foot ceilings. Walk to coffee shops, restaurants, and nightlife.",
        "price": 275000,
        "bedrooms": 0,
        "bathrooms": 1,
        "square_feet": 650,
        "location": "Warehouse District",
        "address": "300 Colorado Street, Unit 205",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
    },
    {
        "title": "Classic Mueller Home",
        "description": "Energy-efficient 3-bedroom home in master-planned Mueller community. "
        "Solar panels, tankless water heater, drought-tolerant landscaping. Near trails and parks.",
        "price": 550000,
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 1650,
        "location": "Mueller",
        "address": "45 Aldrich Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78723",
    },
    {
        "title": "Barton Hills Gem",
        "description": "Updated 3-bedroom home in desirable Barton Hills. Huge backyard backing to greenbelt, "
        "updated kitchen and baths, tons of natural light. Minutes to Zilker Park and downtown.",
        "price": 725000,
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 1900,
        "location": "Barton Hills",
        "address": "2100 Barton Hills Drive",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78704",
    },
]


async def seed_database():
    """Seed the database with sample properties."""
    await init_db()
    logger.info("Database initialized")

    async with async_session_maker() as session:
        for prop_data in SAMPLE_PROPERTIES:
            property_obj = Property(**prop_data)
            session.add(property_obj)

        await session.commit()
        logger.info(f"Added {len(SAMPLE_PROPERTIES)} properties to database")


async def index_properties():
    """Index all properties in Pinecone."""
    if not settings.pinecone_api_key:
        logger.warning("Pinecone API key not set, skipping indexing")
        return

    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set (needed for embeddings), skipping indexing")
        return

    search_service = SearchService()
    count = await search_service.index_all_properties()
    logger.info(f"Indexed {count} properties in Pinecone")


async def main():
    """Main entry point."""
    logger.info("Starting database seeding...")

    await seed_database()
    await index_properties()

    logger.info("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

