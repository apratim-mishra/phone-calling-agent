#!/usr/bin/env python3
"""Set up Pinecone index for property search."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.config import settings
from src.database.pinecone_client import PineconeClient
from src.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Create Pinecone index."""
    if not settings.pinecone_api_key:
        logger.error("PINECONE_API_KEY not set in environment")
        sys.exit(1)

    logger.info(f"Setting up Pinecone index: {settings.pinecone_index_name}")

    client = PineconeClient()

    try:
        client.create_index(dimension=settings.embedding_dimension)
        logger.info("Pinecone index created successfully")

        stats = client.get_stats()
        logger.info(f"Index stats: {stats}")

    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

