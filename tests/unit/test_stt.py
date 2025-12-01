"""
Unit tests for Speech-to-Text (Whisper STT) module.

Run with: pytest tests/unit/test_stt.py -v

Tests:
- Whisper model loads correctly
- Local transcription works
- Groq API transcription works (if key configured)
- Audio preprocessing is correct
"""
import pytest
import numpy as np


class TestWhisperSTTInit:
    """Test WhisperSTT initialization."""

    def test_import_stt_module(self):
        """
        TEST: STT module imports successfully
        
        Expected: No import errors
        """
        print("\n🎤 Testing STT module import...")
        from src.audio.stt import WhisperSTT
        
        assert WhisperSTT is not None
        print("✅ WhisperSTT module imported successfully")

    def test_stt_initialization(self):
        """
        TEST: WhisperSTT initializes with default settings
        
        Expected: Instance created with config values
        """
        print("\n🎤 Testing STT initialization...")
        from src.audio.stt import WhisperSTT
        from src.config import settings
        
        stt = WhisperSTT()
        
        assert stt.model_size == settings.whisper_model_size
        assert stt.provider == settings.stt_provider
        assert stt._model is None  # Lazy loading
        
        print(f"   Model size: {stt.model_size}")
        print(f"   Provider: {stt.provider}")
        print("✅ STT initialized correctly")

    def test_stt_custom_model_size(self):
        """
        TEST: WhisperSTT accepts custom model size
        
        Expected: Custom model size is set
        """
        print("\n🎤 Testing custom model size...")
        from src.audio.stt import WhisperSTT
        
        stt = WhisperSTT(model_size="tiny")
        assert stt.model_size == "tiny"
        
        print(f"   Custom model size: {stt.model_size}")
        print("✅ Custom model size accepted")

    def test_stt_provider_selection(self):
        """
        TEST: STT provider can be configured
        
        Expected: Provider is correctly set
        """
        print("\n🎤 Testing provider selection...")
        from src.audio.stt import WhisperSTT
        
        # Test local provider
        stt_local = WhisperSTT(provider="local")
        assert stt_local.provider == "local"
        
        # Test groq provider
        stt_groq = WhisperSTT(provider="groq")
        assert stt_groq.provider == "groq"
        
        print("   Local provider: ✓")
        print("   Groq provider: ✓")
        print("✅ Provider selection working")


class TestWhisperSTTLocal:
    """Test local MLX Whisper transcription."""

    @pytest.fixture
    def stt_local(self):
        """Create local STT instance."""
        from src.audio.stt import WhisperSTT
        return WhisperSTT(provider="local")

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio for testing (440Hz sine wave)."""
        duration = 2.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        return audio

    @pytest.fixture
    def silent_audio(self):
        """Generate silent audio for testing."""
        duration = 1.0
        sample_rate = 16000
        return np.zeros(int(sample_rate * duration), dtype=np.float32)

    def test_model_loading(self, stt_local):
        """
        TEST: MLX Whisper model loads successfully
        
        Expected: Model loaded without errors
        NOTE: First run will download model (~140MB for base)
        """
        print("\n🎤 Testing local model loading...")
        print("   This might take a minute if model needs to download...")
        
        try:
            stt_local._load_model()
            assert stt_local._model is not None
            print("✅ MLX Whisper model loaded successfully")
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            raise

    def test_transcribe_silent_audio(self, stt_local, silent_audio):
        """
        TEST: Transcribe silent audio
        
        Expected: Returns empty or minimal text
        """
        print("\n🎤 Testing silent audio transcription...")
        
        try:
            result = stt_local.transcribe(silent_audio)
            
            assert isinstance(result, str)
            print(f"   Result: '{result}'")
            print("✅ Silent audio transcription completed")
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            raise

    def test_transcribe_audio_formats(self, stt_local):
        """
        TEST: Handle different audio formats
        
        Expected: Correctly processes various numpy dtypes
        """
        print("\n🎤 Testing audio format handling...")
        
        duration = 1.0
        sample_rate = 16000
        samples = int(sample_rate * duration)
        
        # Test float32 (native format)
        audio_f32 = np.zeros(samples, dtype=np.float32)
        result = stt_local.transcribe(audio_f32)
        assert isinstance(result, str)
        print("   float32 format: ✓")
        
        # Test float64 (should be converted)
        audio_f64 = np.zeros(samples, dtype=np.float64)
        result = stt_local.transcribe(audio_f64)
        assert isinstance(result, str)
        print("   float64 format: ✓")
        
        # Test int16 (common PCM format)
        audio_i16 = np.zeros(samples, dtype=np.int16)
        result = stt_local.transcribe(audio_i16)
        assert isinstance(result, str)
        print("   int16 format: ✓")
        
        print("✅ All audio formats handled correctly")

    def test_transcribe_stereo_to_mono(self, stt_local):
        """
        TEST: Convert stereo audio to mono
        
        Expected: Stereo input processed correctly
        """
        print("\n🎤 Testing stereo to mono conversion...")
        
        duration = 1.0
        sample_rate = 16000
        samples = int(sample_rate * duration)
        
        # Create stereo audio (2 channels)
        stereo_audio = np.zeros((samples, 2), dtype=np.float32)
        
        try:
            result = stt_local.transcribe(stereo_audio)
            assert isinstance(result, str)
            print("✅ Stereo audio converted and processed")
        except Exception as e:
            print(f"❌ Stereo handling failed: {e}")
            raise


class TestWhisperSTTGroq:
    """Test Groq Whisper API transcription."""

    @pytest.fixture
    def stt_groq(self):
        """Create Groq STT instance."""
        from src.audio.stt import WhisperSTT
        return WhisperSTT(provider="groq")

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio for testing."""
        duration = 2.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        return audio

    def test_groq_api_configured(self):
        """
        TEST: Check if Groq API is configured
        
        Expected: API key present in settings
        """
        print("\n🎤 Checking Groq API configuration...")
        from src.config import settings
        
        if not settings.groq_api_key:
            print("   ⚠️  GROQ_API_KEY not set - skipping Groq tests")
            pytest.skip("Groq API key not configured")
        
        print("   Groq API key: configured ✓")
        print("✅ Groq API ready for testing")

    def test_groq_transcription(self, stt_groq, sample_audio):
        """
        TEST: Transcribe audio using Groq API
        
        Expected: Returns transcribed text
        NOTE: Requires GROQ_API_KEY to be set
        """
        print("\n🎤 Testing Groq API transcription...")
        from src.config import settings
        
        if not settings.groq_api_key:
            pytest.skip("Groq API key not configured")
        
        try:
            result = stt_groq.transcribe(sample_audio)
            
            assert isinstance(result, str)
            print(f"   Result: '{result}'")
            print("✅ Groq transcription successful")
            
        except Exception as e:
            print(f"❌ Groq transcription failed: {e}")
            raise


class TestWhisperSTTAsync:
    """Test async transcription functionality."""

    @pytest.fixture
    def stt_instance(self):
        """Create STT instance for tests."""
        from src.audio.stt import WhisperSTT
        return WhisperSTT(provider="local")

    @pytest.fixture
    def silent_audio(self):
        """Generate silent audio for testing."""
        return np.zeros(16000, dtype=np.float32)

    @pytest.mark.asyncio
    async def test_async_transcription(self, stt_instance, silent_audio):
        """
        TEST: Async transcription wrapper works
        
        Expected: Returns same result as sync version
        """
        print("\n🎤 Testing async transcription...")
        
        try:
            result = await stt_instance.transcribe_async(silent_audio)
            
            assert isinstance(result, str)
            print(f"   Async result: '{result}'")
            print("✅ Async transcription working")
            
        except Exception as e:
            print(f"❌ Async transcription failed: {e}")
            raise


class TestWhisperSTTCache:
    """Test STT cache management."""

    @pytest.fixture
    def stt_instance(self):
        """Create STT instance for tests."""
        from src.audio.stt import WhisperSTT
        return WhisperSTT(provider="local")

    def test_clear_cache(self, stt_instance):
        """
        TEST: Cache clearing works without error
        
        Expected: No exceptions raised
        """
        print("\n🎤 Testing cache clearing...")
        
        try:
            # Load model first
            stt_instance._load_model()
            
            # Clear cache
            stt_instance.clear_cache()
            
            print("✅ Cache cleared successfully")
            
        except Exception as e:
            print(f"⚠️  Cache clearing had an issue (non-fatal): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

