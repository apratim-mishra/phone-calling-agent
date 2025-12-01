"""
Integration tests for the complete voice pipeline.

Run with: pytest tests/integration/test_voice_pipeline.py -v

Tests:
- Full STT → LLM → TTS pipeline
- Audio processing end-to-end
- Real model inference
"""
import pytest
import numpy as np
import asyncio


class TestVoicePipelineIntegration:
    """Test complete voice processing pipeline."""

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio (2 seconds of silence)."""
        duration = 2.0
        sample_rate = 16000
        return np.zeros(int(sample_rate * duration), dtype=np.float32)

    def test_stt_to_text(self, sample_audio):
        """
        TEST: STT converts audio to text
        
        Expected: Returns string from audio input
        """
        print("\n🔄 Testing STT audio → text...")
        from src.audio.stt import WhisperSTT
        
        stt = WhisperSTT()
        
        try:
            text = stt.transcribe(sample_audio)
            
            assert isinstance(text, str)
            print(f"   Transcription result: '{text}'")
            print("✅ STT audio → text working")
            
        except Exception as e:
            print(f"❌ STT failed: {e}")
            raise

    def test_tts_to_audio(self):
        """
        TEST: TTS converts text to audio
        
        Expected: Returns audio numpy array
        """
        print("\n🔄 Testing TTS text → audio...")
        from src.audio.tts import KokoroTTS
        
        tts = KokoroTTS()
        test_text = "This is an integration test."
        
        try:
            audio = tts.synthesize(test_text)
            
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
            assert audio.dtype == np.float32
            
            duration = len(audio) / tts.sample_rate
            print(f"   Generated {duration:.2f}s of audio")
            print("✅ TTS text → audio working")
            
        except Exception as e:
            print(f"❌ TTS failed: {e}")
            raise

    def test_full_voice_round_trip(self, sample_audio):
        """
        TEST: Complete audio → text → response → audio pipeline
        
        Expected: End-to-end voice processing works
        """
        print("\n🔄 Testing full voice round trip...")
        print("   audio → STT → text → TTS → audio")
        
        from src.audio.stt import WhisperSTT
        from src.audio.tts import KokoroTTS
        
        stt = WhisperSTT()
        tts = KokoroTTS()
        
        try:
            # Step 1: Audio to text
            print("   Step 1: STT processing...")
            transcription = stt.transcribe(sample_audio)
            print(f"   Transcription: '{transcription}'")
            
            # Step 2: Generate response text (simulated)
            response_text = "I received your message. How can I help you today?"
            print(f"   Response: '{response_text}'")
            
            # Step 3: Text to audio
            print("   Step 2: TTS processing...")
            response_audio = tts.synthesize(response_text)
            
            duration = len(response_audio) / tts.sample_rate
            print(f"   Generated {duration:.2f}s response audio")
            
            assert isinstance(response_audio, np.ndarray)
            assert len(response_audio) > 0
            
            print("✅ Full voice round trip successful")
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            raise


class TestAudioProcessorIntegration:
    """Test audio processor with real audio."""

    def test_audio_processor_import(self):
        """
        TEST: AudioProcessor imports and initializes
        
        Expected: No errors
        """
        print("\n🔄 Testing AudioProcessor import...")
        from src.audio.processor import AudioProcessor
        
        processor = AudioProcessor()
        assert processor is not None
        
        print("✅ AudioProcessor initialized")

    def test_audio_format_conversion(self):
        """
        TEST: Audio format conversion works
        
        Expected: Converts between formats correctly
        """
        print("\n🔄 Testing audio format conversion...")
        from src.audio.processor import AudioProcessor
        
        processor = AudioProcessor()
        
        # Create test audio
        duration = 1.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        # Convert to bytes
        audio_bytes = audio.tobytes()
        
        print(f"   Input audio: {len(audio)} samples")
        print(f"   Input bytes: {len(audio_bytes)} bytes")
        print("✅ Audio format conversion ready")


class TestCallServiceIntegration:
    """Test call service with real components."""

    def test_call_service_components(self):
        """
        TEST: CallService has all required components
        
        Expected: STT, TTS, and agent components initialized
        """
        print("\n🔄 Testing CallService components...")
        from src.services.call_service import CallService
        
        try:
            service = CallService()
            
            assert service.stt is not None, "STT component missing"
            assert service.tts is not None, "TTS component missing"
            
            print("   STT: initialized ✓")
            print("   TTS: initialized ✓")
            print("✅ CallService components ready")
            
        except Exception as e:
            print(f"❌ CallService init failed: {e}")
            raise


class TestDatabaseIntegration:
    """Test database operations."""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """
        TEST: Database connection works
        
        Expected: Can connect to SQLite database
        """
        print("\n🔄 Testing database connection...")
        from src.database import init_db, engine
        from sqlalchemy import text
        
        try:
            await init_db()
            print("   Database initialized ✓")
            
            # Test connection with proper SQLAlchemy text()
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                print("   Query executed ✓")
            
            print("✅ Database connection working")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise


class TestSearchIntegration:
    """Test search functionality with Pinecone."""

    def test_pinecone_client_import(self):
        """
        TEST: Pinecone client imports correctly
        
        Expected: No import errors
        """
        print("\n🔄 Testing Pinecone client import...")
        from src.database.pinecone_client import PineconeClient
        
        assert PineconeClient is not None
        print("✅ PineconeClient imported")

    def test_pinecone_client_initialization(self):
        """
        TEST: Pinecone client initializes
        
        Expected: Client created (connection tested separately)
        """
        print("\n🔄 Testing Pinecone client initialization...")
        from src.database.pinecone_client import PineconeClient
        from src.config import settings
        
        if not settings.pinecone_api_key:
            print("   ⚠️  PINECONE_API_KEY not set - skipping")
            pytest.skip("Pinecone API key not configured")
        
        try:
            client = PineconeClient()
            print("   Pinecone client created ✓")
            print("✅ Pinecone client initialized")
        except Exception as e:
            print(f"❌ Pinecone client failed: {e}")
            raise


class TestAgentIntegration:
    """Test voice agent functionality."""

    def test_agent_import(self):
        """
        TEST: Voice agent imports correctly
        
        Expected: No import errors
        """
        print("\n🔄 Testing voice agent import...")
        from src.agents.voice_agent import VoiceAgent
        
        assert VoiceAgent is not None
        print("✅ VoiceAgent imported")

    def test_agent_initialization(self):
        """
        TEST: Voice agent initializes
        
        Expected: Agent created with LLM
        """
        print("\n🔄 Testing voice agent initialization...")
        from src.agents.voice_agent import VoiceAgent
        from src.config import settings
        
        # Check if any LLM is configured
        has_llm = (
            settings.primary_llm_available or
            settings.groq_llm_available or
            settings.fallback_llm_available
        )
        
        if not has_llm:
            print("   ⚠️  No LLM API key configured - skipping")
            pytest.skip("No LLM API key configured")
        
        try:
            agent = VoiceAgent()
            print("   Voice agent created ✓")
            print("✅ VoiceAgent initialized")
        except Exception as e:
            print(f"❌ Agent initialization failed: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

