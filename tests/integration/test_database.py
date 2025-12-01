"""
Integration tests for database operations.

Run with: pytest tests/integration/test_database.py -v

Tests:
- SQLite database operations
- Property model CRUD
- Call log model CRUD
"""
import pytest
import pytest_asyncio
from datetime import datetime


class TestDatabaseModels:
    """Test database model imports."""

    def test_import_models(self):
        """
        TEST: Database models import correctly
        
        Expected: No import errors
        """
        print("\n💾 Testing database model imports...")
        from src.database.models import Property, CallLog
        
        assert Property is not None
        assert CallLog is not None
        
        print("   Property model: ✓")
        print("   CallLog model: ✓")
        print("✅ Models imported successfully")

    def test_import_base(self):
        """
        TEST: Database base imports correctly
        
        Expected: No import errors
        """
        print("\n💾 Testing database base import...")
        from src.database import Base
        
        assert Base is not None
        print("✅ Database Base imported")


class TestDatabaseSetup:
    """Test database initialization."""

    @pytest.mark.asyncio
    async def test_init_db(self):
        """
        TEST: Database initialization creates tables
        
        Expected: Tables created without error
        """
        print("\n💾 Testing database initialization...")
        from src.database import init_db
        
        try:
            await init_db()
            print("   Tables created ✓")
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database init failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_get_session(self):
        """
        TEST: Database session can be acquired
        
        Expected: Session returned from async generator
        """
        print("\n💾 Testing database session...")
        from src.database import get_session
        
        try:
            async for session in get_session():
                assert session is not None
                print("   Session acquired ✓")
                break
            print("✅ Database session working")
        except Exception as e:
            print(f"❌ Session acquisition failed: {e}")
            raise


class TestPropertyModel:
    """Test Property model operations."""

    @pytest_asyncio.fixture
    async def db_session(self):
        """Create test database session."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from src.database import Base
        
        # Use in-memory SQLite for tests
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_maker() as session:
            yield session
        
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_create_property(self, db_session):
        """
        TEST: Create a property record
        
        Expected: Property saved to database
        """
        print("\n💾 Testing property creation...")
        from src.database.models import Property
        
        # Provide ALL required fields
        property_data = Property(
            title="Test Property",
            description="A beautiful test property with great views",
            price=500000.0,
            bedrooms=3,
            bathrooms=2.0,
            square_feet=2000,
            location="Downtown Austin",
            address="123 Test Street",
            city="Austin",
            state="TX",
            zip_code="78701"
        )
        
        db_session.add(property_data)
        await db_session.commit()
        await db_session.refresh(property_data)
        
        assert property_data.id is not None
        print(f"   Created property ID: {property_data.id}")
        print(f"   Title: {property_data.title}")
        print("✅ Property created successfully")

    @pytest.mark.asyncio
    async def test_query_property(self, db_session):
        """
        TEST: Query property from database
        
        Expected: Property retrieved correctly
        """
        print("\n💾 Testing property query...")
        from src.database.models import Property
        from sqlalchemy import select
        
        # Create property with ALL required fields
        prop = Property(
            title="Query Test Property",
            description="A test property for query testing",
            price=300000.0,
            bedrooms=2,
            bathrooms=1.0,
            square_feet=1500,
            location="North Dallas",
            address="456 Test Avenue",
            city="Dallas",
            state="TX",
            zip_code="75201"
        )
        db_session.add(prop)
        await db_session.commit()
        
        # Query it back
        result = await db_session.execute(
            select(Property).where(Property.title == "Query Test Property")
        )
        queried = result.scalar_one_or_none()
        
        assert queried is not None
        assert queried.title == "Query Test Property"
        assert queried.price == 300000.0
        
        print(f"   Found property: {queried.title}")
        print("✅ Property query successful")


class TestCallLogModel:
    """Test CallLog model operations."""

    @pytest_asyncio.fixture
    async def db_session(self):
        """Create test database session."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from src.database import Base
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_maker() as session:
            yield session
        
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_create_call_log(self, db_session):
        """
        TEST: Create a call log record
        
        Expected: Call log saved to database
        """
        print("\n💾 Testing call log creation...")
        from src.database.models import CallLog, CallDirection, CallStatus
        
        # Use proper enum values
        call_log = CallLog(
            call_sid="CA123456789",
            direction=CallDirection.INBOUND,
            from_number="+1234567890",
            to_number="+0987654321",
            status=CallStatus.COMPLETED,
            duration=120,
            transcription="Hello, I am looking for a property.",
            summary="Customer inquiry about properties"
        )
        
        db_session.add(call_log)
        await db_session.commit()
        await db_session.refresh(call_log)
        
        assert call_log.id is not None
        print(f"   Created call log ID: {call_log.id}")
        print(f"   Call SID: {call_log.call_sid}")
        print("✅ Call log created successfully")

    @pytest.mark.asyncio
    async def test_query_call_log(self, db_session):
        """
        TEST: Query call log from database
        
        Expected: Call log retrieved correctly
        """
        print("\n💾 Testing call log query...")
        from src.database.models import CallLog, CallDirection, CallStatus
        from sqlalchemy import select
        
        # Create call log with proper enums
        log = CallLog(
            call_sid="CA987654321",
            direction=CallDirection.OUTBOUND,
            from_number="+1111111111",
            to_number="+2222222222",
            status=CallStatus.COMPLETED
        )
        db_session.add(log)
        await db_session.commit()
        
        # Query it back
        result = await db_session.execute(
            select(CallLog).where(CallLog.call_sid == "CA987654321")
        )
        queried = result.scalar_one_or_none()
        
        assert queried is not None
        assert queried.call_sid == "CA987654321"
        assert queried.direction == CallDirection.OUTBOUND
        
        print(f"   Found call log: {queried.call_sid}")
        print("✅ Call log query successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
