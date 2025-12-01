"""
Test configuration and fixtures.

This file is loaded automatically by pytest.
Fixtures are available to all test files.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


# Use in-memory SQLite for tests (avoids .env database URL issues)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session using in-memory SQLite.
    
    This fixture:
    1. Creates an in-memory database
    2. Imports models to register them
    3. Creates all tables
    4. Yields a session for testing
    5. Cleans up after test
    """
    # Import Base here to avoid loading main app at module level
    from src.database import Base
    
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client():
    """
    Create test client for FastAPI app.
    
    Import is done here to avoid loading app at module level,
    which would trigger database initialization.
    """
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


@pytest.fixture
def sample_property_data() -> dict:
    """Sample property data for testing."""
    return {
        "title": "Test Property",
        "description": "A beautiful test property",
        "price": 500000,
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 2000,
        "location": "Test Location",
        "address": "123 Test Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
    }


@pytest.fixture
def sample_audio_bytes() -> bytes:
    """Sample audio data for testing (440Hz sine wave)."""
    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)
    return (audio * 32767).astype(np.int16).tobytes()


@pytest.fixture
def sample_audio_float() -> np.ndarray:
    """Sample audio as float32 numpy array."""
    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    return np.sin(2 * np.pi * 440 * t).astype(np.float32)


@pytest.fixture
def silent_audio() -> np.ndarray:
    """Silent audio for testing (1 second)."""
    sample_rate = 16000
    return np.zeros(sample_rate, dtype=np.float32)
