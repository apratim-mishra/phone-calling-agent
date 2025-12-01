from typing import Optional, Generator
from pathlib import Path

import numpy as np

from src.config import settings
from src.utils.errors import TTSError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class KokoroTTS:
    """Text-to-speech using Kokoro with MLX backend."""

    def __init__(
        self,
        model: Optional[str] = None,
        voice: Optional[str] = None,
    ):
        self.model_name = model or settings.tts_model
        self.voice = voice or settings.tts_voice
        self._pipeline = None
        self._sample_rate = 24000

    def _load_model(self) -> None:
        """Lazy load the Kokoro TTS pipeline."""
        if self._pipeline is not None:
            return

        try:
            from kokoro import KPipeline

            logger.info(f"Loading Kokoro TTS model: {self.model_name}")
            self._pipeline = KPipeline(lang_code="a")
            logger.info("Kokoro TTS model loaded successfully")
        except Exception as e:
            raise TTSError(f"Failed to load Kokoro TTS model: {e}")

    def synthesize(self, text: str, speed: float = 1.0) -> np.ndarray:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            speed: Speech speed multiplier

        Returns:
            Audio as float32 numpy array at 24kHz
        """
        self._load_model()

        try:
            if not text.strip():
                return np.array([], dtype=np.float32)

            logger.info(f"🔊 TTS synthesizing: '{text[:50]}...'")
            audio_segments = []
            generator = self._pipeline(text, voice=self.voice, speed=speed)

            for _, _, audio in generator:
                if audio is not None:
                    # Convert mlx array to numpy if needed
                    if hasattr(audio, 'tolist'):  # mlx array
                        audio = np.array(audio.tolist(), dtype=np.float32)
                    elif not isinstance(audio, np.ndarray):
                        audio = np.array(audio, dtype=np.float32)
                    audio_segments.append(audio)

            if not audio_segments:
                raise TTSError("No audio generated")

            combined = np.concatenate(audio_segments)
            duration = len(combined) / self._sample_rate
            logger.info(f"🔊 TTS generated {duration:.2f}s of audio ({len(combined)} samples)")
            return combined.astype(np.float32)

        except TTSError:
            raise
        except Exception as e:
            raise TTSError(f"TTS synthesis failed: {e}")

    def synthesize_stream(
        self, text: str, speed: float = 1.0
    ) -> Generator[np.ndarray, None, None]:
        """Stream synthesized audio chunks.

        Args:
            text: Text to synthesize
            speed: Speech speed multiplier

        Yields:
            Audio chunks as float32 numpy arrays
        """
        self._load_model()

        try:
            generator = self._pipeline(text, voice=self.voice, speed=speed)

            for _, _, audio in generator:
                if audio is not None:
                    yield audio

        except Exception as e:
            raise TTSError(f"TTS streaming failed: {e}")

    async def synthesize_async(self, text: str, speed: float = 1.0) -> np.ndarray:
        """Async wrapper for synthesis."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.synthesize(text, speed))

    @property
    def sample_rate(self) -> int:
        """Get the output sample rate."""
        return self._sample_rate

    def save_audio(self, audio: np.ndarray, filepath: str | Path) -> None:
        """Save audio to file."""
        try:
            import soundfile as sf

            sf.write(str(filepath), audio, self._sample_rate)
            logger.debug(f"Saved audio to {filepath}")
        except Exception as e:
            raise TTSError(f"Failed to save audio: {e}")

    def clear_cache(self) -> None:
        """Clear model cache."""
        try:
            import mlx.core as mx

            mx.clear_cache()
            logger.debug("MLX cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

