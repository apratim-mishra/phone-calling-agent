import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient

from src.database import Base
from src.api.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
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
def client() -> TestClient:
    """Create test client for API."""
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
    """Sample audio data for testing."""
    import numpy as np

    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)
    return (audio * 32767).astype(np.int16).tobytes()

