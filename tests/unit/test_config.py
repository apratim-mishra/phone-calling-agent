"""
Unit tests for configuration module.

Run with: pytest tests/unit/test_config.py -v

Tests:
- Environment variables load correctly
- Default values are set properly
- Settings singleton works
"""
import pytest
from unittest.mock import patch
import os


class TestConfigLoading:
    """Test configuration loading and defaults."""

    def test_settings_import(self):
        """
        TEST: Settings module imports successfully
        
        Expected: No import errors
        """
        print("\n🔧 Testing settings import...")
        from src.config import settings, get_settings, Settings
        
        assert settings is not None
        assert get_settings is not None
        assert Settings is not None
        print("✅ Settings module imported successfully")

    def test_settings_singleton(self):
        """
        TEST: Settings uses singleton pattern (cached)
        
        Expected: Same instance returned each time
        """
        print("\n🔧 Testing settings singleton...")
        from src.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2, "Settings should be cached singleton"
        print("✅ Settings singleton working correctly")

    def test_default_values(self):
        """
        TEST: Default configuration values are set
        
        Expected: All defaults match expected values
        """
        print("\n🔧 Testing default values...")
        from src.config import settings
        
        # App defaults
        assert settings.app_name == "realtime-phone-agent"
        assert settings.app_port == 8000
        assert settings.debug == False
        print(f"   App name: {settings.app_name}")
        print(f"   App port: {settings.app_port}")
        
        # Model defaults
        assert settings.whisper_model_size in ["tiny", "base", "small"]
        assert settings.tts_voice is not None
        print(f"   Whisper model: {settings.whisper_model_size}")
        print(f"   TTS voice: {settings.tts_voice}")
        
        # STT provider
        assert settings.stt_provider in ["local", "groq"]
        print(f"   STT provider: {settings.stt_provider}")
        
        print("✅ All default values are correct")

    def test_audio_settings(self):
        """
        TEST: Audio settings are configured correctly
        
        Expected: Standard audio configuration
        """
        print("\n🔧 Testing audio settings...")
        from src.config import settings
        
        assert settings.audio_sample_rate == 16000, "Sample rate should be 16kHz for Whisper"
        assert settings.audio_channels == 1, "Should be mono audio"
        
        print(f"   Sample rate: {settings.audio_sample_rate}Hz")
        print(f"   Channels: {settings.audio_channels}")
        print("✅ Audio settings correct")


class TestLLMConfiguration:
    """Test LLM provider configuration."""

    def test_llm_availability_properties(self):
        """
        TEST: LLM availability properties work correctly
        
        Expected: Properties return bool based on key presence
        """
        print("\n🔧 Testing LLM availability checks...")
        from src.config import settings
        
        # These are properties that check if keys are set
        primary_available = settings.primary_llm_available
        groq_available = settings.groq_llm_available
        fallback_available = settings.fallback_llm_available
        
        print(f"   Z.ai (primary) available: {primary_available}")
        print(f"   Groq available: {groq_available}")
        print(f"   OpenAI (fallback) available: {fallback_available}")
        
        # At least one should be available if .env is configured
        assert isinstance(primary_available, bool)
        assert isinstance(groq_available, bool)
        assert isinstance(fallback_available, bool)
        
        print("✅ LLM availability checks working")

    def test_groq_settings(self):
        """
        TEST: Groq settings are configured
        
        Expected: Base URL and model are set
        """
        print("\n🔧 Testing Groq settings...")
        from src.config import settings
        
        assert settings.groq_base_url == "https://api.groq.com/openai/v1"
        assert settings.groq_model is not None
        
        print(f"   Groq base URL: {settings.groq_base_url}")
        print(f"   Groq model: {settings.groq_model}")
        print("✅ Groq settings correct")


class TestDatabaseConfiguration:
    """Test database configuration."""

    def test_database_url(self):
        """
        TEST: Database URL is configured
        
        Expected: SQLite URL pattern for development
        """
        print("\n🔧 Testing database configuration...")
        from src.config import settings
        
        assert settings.database_url is not None
        assert "sqlite" in settings.database_url or "postgresql" in settings.database_url
        
        print(f"   Database URL: {settings.database_url}")
        print("✅ Database configuration correct")

    def test_pinecone_settings(self):
        """
        TEST: Pinecone settings are configured
        
        Expected: Index name and embedding settings present
        """
        print("\n🔧 Testing Pinecone settings...")
        from src.config import settings
        
        assert settings.pinecone_index_name is not None
        assert settings.embedding_model is not None
        assert settings.embedding_dimension > 0
        
        print(f"   Index name: {settings.pinecone_index_name}")
        print(f"   Embedding model: {settings.embedding_model}")
        print(f"   Embedding dimension: {settings.embedding_dimension}")
        print("✅ Pinecone settings correct")


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_env_file_loaded(self):
        """
        TEST: .env file is being loaded
        
        Expected: At least some values from .env are present
        """
        print("\n🔧 Testing .env file loading...")
        from src.config import settings
        
        # Check if any API keys are set (indicates .env loaded)
        has_any_key = (
            bool(settings.groq_api_key) or
            bool(settings.openai_api_key) or
            bool(settings.pinecone_api_key) or
            bool(settings.twilio_account_sid)
        )
        
        if has_any_key:
            print("   Found API keys in configuration")
            print("✅ .env file loaded successfully")
        else:
            print("   ⚠️  No API keys found - make sure .env is configured")
            pytest.skip("No API keys configured - skipping env test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

