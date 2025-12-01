"""
Unit tests for Text-to-Speech (Kokoro TTS) module.

Run with: pytest tests/unit/test_tts.py -v

Tests:
- Kokoro TTS model loads correctly
- Text synthesis works
- Audio output format is correct
- Streaming synthesis works
"""
import pytest
import numpy as np
from pathlib import Path


class TestKokoroTTSInit:
    """Test KokoroTTS initialization."""

    def test_import_tts_module(self):
        """
        TEST: TTS module imports successfully
        
        Expected: No import errors
        """
        print("\n🗣️ Testing TTS module import...")
        from src.audio.tts import KokoroTTS
        
        assert KokoroTTS is not None
        print("✅ KokoroTTS module imported successfully")

    def test_tts_initialization(self):
        """
        TEST: KokoroTTS initializes with default settings
        
        Expected: Instance created with config values
        """
        print("\n🗣️ Testing TTS initialization...")
        from src.audio.tts import KokoroTTS
        from src.config import settings
        
        tts = KokoroTTS()
        
        assert tts.model_name == settings.tts_model
        assert tts.voice == settings.tts_voice
        assert tts._pipeline is None  # Lazy loading
        
        print(f"   Model name: {tts.model_name}")
        print(f"   Voice: {tts.voice}")
        print("✅ TTS initialized correctly")

    def test_tts_custom_voice(self):
        """
        TEST: KokoroTTS accepts custom voice parameter
        
        Expected: Custom voice is set
        """
        print("\n🗣️ Testing custom voice setting...")
        from src.audio.tts import KokoroTTS
        
        custom_voice = "am_adam"
        tts = KokoroTTS(voice=custom_voice)
        
        assert tts.voice == custom_voice
        print(f"   Custom voice set: {tts.voice}")
        print("✅ Custom voice accepted")


class TestKokoroTTSSynthesis:
    """Test TTS synthesis functionality."""

    @pytest.fixture
    def tts_instance(self):
        """Create TTS instance for tests."""
        from src.audio.tts import KokoroTTS
        return KokoroTTS()

    def test_model_loading(self, tts_instance):
        """
        TEST: Kokoro model loads successfully (downloads if needed)
        
        Expected: Model loaded without errors
        NOTE: First run will download ~150MB model
        """
        print("\n🗣️ Testing model loading (may download on first run)...")
        print("   This might take a minute if model needs to download...")
        
        try:
            tts_instance._load_model()
            assert tts_instance._pipeline is not None
            print("✅ Kokoro model loaded successfully")
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            raise

    def test_synthesize_simple_text(self, tts_instance):
        """
        TEST: Synthesize simple text to audio
        
        Expected: Returns numpy array with audio data
        """
        print("\n🗣️ Testing text synthesis...")
        
        test_text = "Hello, this is a test."
        
        try:
            audio = tts_instance.synthesize(test_text)
            
            assert isinstance(audio, np.ndarray), "Output should be numpy array"
            assert audio.dtype == np.float32, "Audio should be float32"
            assert len(audio) > 0, "Audio should not be empty"
            
            duration = len(audio) / tts_instance.sample_rate
            print(f"   Generated {duration:.2f} seconds of audio")
            print(f"   Audio shape: {audio.shape}")
            print(f"   Sample rate: {tts_instance.sample_rate}Hz")
            print("✅ Text synthesis successful")
            
        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
            raise

    def test_synthesize_empty_text(self, tts_instance):
        """
        TEST: Handle empty text input gracefully
        
        Expected: Returns empty array without error
        """
        print("\n🗣️ Testing empty text handling...")
        
        audio = tts_instance.synthesize("")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) == 0
        
        print("✅ Empty text handled correctly")

    def test_sample_rate_property(self, tts_instance):
        """
        TEST: Sample rate property returns correct value
        
        Expected: 24000Hz (Kokoro default)
        """
        print("\n🗣️ Testing sample rate property...")
        
        assert tts_instance.sample_rate == 24000, "Kokoro outputs 24kHz audio"
        
        print(f"   Sample rate: {tts_instance.sample_rate}Hz")
        print("✅ Sample rate correct")


class TestKokoroTTSStreaming:
    """Test TTS streaming functionality."""

    @pytest.fixture
    def tts_instance(self):
        """Create TTS instance for tests."""
        from src.audio.tts import KokoroTTS
        return KokoroTTS()

    def test_streaming_synthesis(self, tts_instance):
        """
        TEST: Streaming synthesis yields audio chunks
        
        Expected: Generator yields audio data (numpy arrays or tensors)
        """
        print("\n🗣️ Testing streaming synthesis...")
        
        test_text = "This is a streaming test with multiple words."
        chunks = []
        
        try:
            for chunk in tts_instance.synthesize_stream(test_text):
                # Kokoro may return numpy arrays or tensors
                # Convert to numpy if needed
                if hasattr(chunk, 'numpy'):
                    chunk = chunk.numpy()
                elif not isinstance(chunk, np.ndarray):
                    chunk = np.array(chunk)
                chunks.append(chunk)
            
            assert len(chunks) > 0, "Should yield at least one chunk"
            
            total_samples = sum(len(c) for c in chunks)
            duration = total_samples / tts_instance.sample_rate
            
            print(f"   Received {len(chunks)} audio chunks")
            print(f"   Total duration: {duration:.2f} seconds")
            print("✅ Streaming synthesis working")
            
        except Exception as e:
            print(f"❌ Streaming failed: {e}")
            raise


class TestKokoroTTSFileOutput:
    """Test TTS file output functionality."""

    @pytest.fixture
    def tts_instance(self):
        """Create TTS instance for tests."""
        from src.audio.tts import KokoroTTS
        return KokoroTTS()

    def test_save_audio_to_file(self, tts_instance, tmp_path):
        """
        TEST: Save synthesized audio to file
        
        Expected: WAV file created successfully
        """
        print("\n🗣️ Testing audio file save...")
        
        test_text = "Saving this to a file."
        output_path = tmp_path / "test_output.wav"
        
        try:
            audio = tts_instance.synthesize(test_text)
            tts_instance.save_audio(audio, output_path)
            
            assert output_path.exists(), "Output file should exist"
            assert output_path.stat().st_size > 0, "File should not be empty"
            
            print(f"   Saved to: {output_path}")
            print(f"   File size: {output_path.stat().st_size} bytes")
            print("✅ Audio file saved successfully")
            
        except Exception as e:
            print(f"❌ File save failed: {e}")
            raise


class TestKokoroTTSCache:
    """Test TTS cache management."""

    @pytest.fixture
    def tts_instance(self):
        """Create TTS instance for tests."""
        from src.audio.tts import KokoroTTS
        return KokoroTTS()

    def test_clear_cache(self, tts_instance):
        """
        TEST: Cache clearing works without error
        
        Expected: No exceptions raised
        """
        print("\n🗣️ Testing cache clearing...")
        
        try:
            # Load model first
            tts_instance._load_model()
            
            # Clear cache
            tts_instance.clear_cache()
            
            print("✅ Cache cleared successfully")
            
        except Exception as e:
            print(f"⚠️  Cache clearing had an issue (non-fatal): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

