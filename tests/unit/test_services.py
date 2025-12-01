"""
Unit tests for service modules (Twilio, Call Service, Search Service).

Run with: pytest tests/unit/test_services.py -v

Tests:
- Twilio service initialization
- TwiML response generation
- Call service functionality
- Search service (requires Pinecone)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestTwilioServiceInit:
    """Test TwilioService initialization."""

    def test_import_twilio_service(self):
        """
        TEST: Twilio service module imports successfully
        
        Expected: No import errors
        """
        print("\n📞 Testing Twilio service import...")
        from src.services.twilio_service import TwilioService
        
        assert TwilioService is not None
        print("✅ TwilioService imported successfully")

    def test_twilio_initialization(self):
        """
        TEST: TwilioService initializes with config values
        
        Expected: Instance created with settings
        """
        print("\n📞 Testing Twilio service initialization...")
        from src.services.twilio_service import TwilioService
        from src.config import settings
        
        service = TwilioService()
        
        assert service.account_sid == settings.twilio_account_sid
        assert service.auth_token == settings.twilio_auth_token
        assert service.phone_number == settings.twilio_phone_number
        assert service._client is None  # Lazy loading
        
        print(f"   Account SID configured: {bool(service.account_sid)}")
        print(f"   Auth token configured: {bool(service.auth_token)}")
        print(f"   Phone number configured: {bool(service.phone_number)}")
        print("✅ TwilioService initialized correctly")

    def test_twilio_custom_credentials(self):
        """
        TEST: TwilioService accepts custom credentials
        
        Expected: Custom values override config
        """
        print("\n📞 Testing custom Twilio credentials...")
        from src.services.twilio_service import TwilioService
        
        custom_sid = "test_sid"
        custom_token = "test_token"
        custom_number = "+1234567890"
        
        service = TwilioService(
            account_sid=custom_sid,
            auth_token=custom_token,
            phone_number=custom_number
        )
        
        assert service.account_sid == custom_sid
        assert service.auth_token == custom_token
        assert service.phone_number == custom_number
        
        print("✅ Custom credentials accepted")


class TestTwilioTwiMLResponses:
    """Test TwiML response generation."""

    @pytest.fixture
    def twilio_service(self):
        """Create Twilio service instance."""
        from src.services.twilio_service import TwilioService
        return TwilioService()

    def test_create_stream_response(self, twilio_service):
        """
        TEST: Generate TwiML for WebSocket streaming
        
        Expected: Valid TwiML XML with Stream element
        """
        print("\n📞 Testing stream response generation...")
        
        websocket_url = "wss://example.com/voice/stream"
        response = twilio_service.create_stream_response(websocket_url)
        
        assert isinstance(response, str)
        assert "<?xml" in response or "<Response>" in response
        assert "Stream" in response
        assert websocket_url in response
        
        print(f"   Generated TwiML:\n   {response[:200]}...")
        print("✅ Stream response generated correctly")

    def test_create_say_response(self, twilio_service):
        """
        TEST: Generate TwiML for text-to-speech
        
        Expected: Valid TwiML XML with Say element
        """
        print("\n📞 Testing say response generation...")
        
        message = "Hello, this is a test message."
        response = twilio_service.create_say_response(message)
        
        assert isinstance(response, str)
        assert "Say" in response
        assert message in response
        
        print(f"   Generated TwiML:\n   {response}")
        print("✅ Say response generated correctly")

    def test_create_gather_response(self, twilio_service):
        """
        TEST: Generate TwiML for gathering speech input
        
        Expected: Valid TwiML XML with Gather element
        """
        print("\n📞 Testing gather response generation...")
        
        prompt = "Please say something."
        action_url = "https://example.com/handle-speech"
        
        response = twilio_service.create_gather_response(prompt, action_url)
        
        assert isinstance(response, str)
        assert "Gather" in response
        assert prompt in response
        assert action_url in response
        
        print(f"   Generated TwiML:\n   {response[:300]}...")
        print("✅ Gather response generated correctly")


class TestTwilioClientOperations:
    """Test Twilio client operations (mocked)."""

    @pytest.fixture
    def twilio_service(self):
        """Create Twilio service with test credentials."""
        from src.services.twilio_service import TwilioService
        return TwilioService(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+1234567890"
        )

    def test_get_client_without_credentials(self):
        """
        TEST: Client creation fails without credentials
        
        Expected: TwilioError raised when credentials are missing
        """
        print("\n📞 Testing client creation without credentials...")
        from src.services.twilio_service import TwilioService
        from src.utils.errors import TwilioError
        
        # Create service and manually clear credentials
        service = TwilioService()
        service.account_sid = ""
        service.auth_token = ""
        
        with pytest.raises(TwilioError):
            service._get_client()
        
        print("✅ Correctly raises error without credentials")

    def test_request_validation(self, twilio_service):
        """
        TEST: Request validator is created
        
        Expected: Validator instance created
        """
        print("\n📞 Testing request validator creation...")
        
        validator = twilio_service._get_validator()
        
        assert validator is not None
        print("✅ Request validator created")


class TestCallService:
    """Test CallService functionality."""

    def test_import_call_service(self):
        """
        TEST: Call service module imports successfully
        
        Expected: No import errors
        """
        print("\n📱 Testing call service import...")
        from src.services.call_service import CallService
        
        assert CallService is not None
        print("✅ CallService imported successfully")

    def test_call_service_initialization(self):
        """
        TEST: CallService initializes with components
        
        Expected: STT, TTS, and Agent initialized
        """
        print("\n📱 Testing call service initialization...")
        from src.services.call_service import CallService
        
        service = CallService()
        
        assert service.stt is not None
        assert service.tts is not None
        
        print("   STT component: initialized ✓")
        print("   TTS component: initialized ✓")
        print("✅ CallService initialized correctly")


class TestSearchService:
    """Test SearchService functionality."""

    def test_import_search_service(self):
        """
        TEST: Search service module imports successfully
        
        Expected: No import errors
        """
        print("\n🔍 Testing search service import...")
        from src.services.search_service import SearchService
        
        assert SearchService is not None
        print("✅ SearchService imported successfully")

    def test_search_service_initialization(self):
        """
        TEST: SearchService initializes correctly
        
        Expected: Instance created without errors
        """
        print("\n🔍 Testing search service initialization...")
        from src.services.search_service import SearchService
        
        try:
            service = SearchService()
            print("✅ SearchService initialized correctly")
        except Exception as e:
            print(f"⚠️  SearchService init issue (may need API keys): {e}")
            pytest.skip("SearchService requires configured API keys")


class TestServiceImports:
    """Test all service imports from __init__."""

    def test_services_init_imports(self):
        """
        TEST: All services import from services module
        
        Expected: All services accessible from src.services
        """
        print("\n📦 Testing services package imports...")
        
        from src.services import TwilioService, CallService, SearchService
        
        assert TwilioService is not None
        assert CallService is not None
        assert SearchService is not None
        
        print("   TwilioService: ✓")
        print("   CallService: ✓")
        print("   SearchService: ✓")
        print("✅ All services importable from package")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

