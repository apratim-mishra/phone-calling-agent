from typing import Optional
import io

import numpy as np
import httpx

from src.config import settings
from src.utils.errors import TranscriptionError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WhisperSTT:
    """Speech-to-text using MLX Whisper (local) or Groq Whisper API (cloud)."""

    def __init__(
        self,
        model_size: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        self.model_size = model_size or settings.whisper_model_size
        self.provider = provider or settings.stt_provider
        self._model = None
        self._processor = None

    def _load_model(self) -> None:
        """Lazy load the Whisper model (local only)."""
        if self._model is not None or self.provider != "local":
            return

        try:
            import mlx_whisper

            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = mlx_whisper
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            raise TranscriptionError(f"Failed to load Whisper model: {e}")

    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "en",
        sample_rate: int = 16000,
    ) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data as float32 numpy array
            language: Language code for transcription
            sample_rate: Sample rate of audio (default 16000 for Whisper)

        Returns:
            Transcribed text
        """
        if self.provider == "groq":
            import asyncio
            return asyncio.get_event_loop().run_until_complete(
                self._transcribe_groq(audio, language, sample_rate)
            )

        return self._transcribe_local(audio, language, sample_rate)

    def _transcribe_local(
        self,
        audio: np.ndarray,
        language: str = "en",
        sample_rate: int = 16000,
    ) -> str:
        """Transcribe using local MLX Whisper."""
        self._load_model()

        try:
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            model_name = f"mlx-community/whisper-{self.model_size}-mlx"

            result = self._model.transcribe(
                audio,
                path_or_hf_repo=model_name,
                language=language,
            )

            text = result.get("text", "").strip()
            logger.debug(f"Transcription (local): {text[:100]}...")
            return text

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}", {"model": self.model_size})

    async def _transcribe_groq(
        self,
        audio: np.ndarray,
        language: str = "en",
        sample_rate: int = 16000,
    ) -> str:
        """Transcribe using Groq Whisper API."""
        if not settings.groq_api_key:
            raise TranscriptionError("Groq API key not configured for STT")

        try:
            import soundfile as sf

            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format="WAV")
            buffer.seek(0)
            audio_bytes = buffer.read()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                    files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                    data={
                        "model": "whisper-large-v3",
                        "language": language,
                        "response_format": "json",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()

            text = result.get("text", "").strip()
            logger.debug(f"Transcription (Groq): {text[:100]}...")
            return text

        except httpx.HTTPError as e:
            raise TranscriptionError(f"Groq API request failed: {e}")
        except Exception as e:
            raise TranscriptionError(f"Groq transcription failed: {e}")

    async def transcribe_async(
        self,
        audio: np.ndarray,
        language: str = "en",
        sample_rate: int = 16000,
    ) -> str:
        """Async wrapper for transcription."""
        if self.provider == "groq":
            return await self._transcribe_groq(audio, language, sample_rate)

        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._transcribe_local(audio, language, sample_rate)
        )

    def clear_cache(self) -> None:
        """Clear MLX cache to free memory."""
        if self.provider != "local":
            return

        try:
            import mlx.core as mx
            mx.clear_cache()
            logger.debug("MLX cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear MLX cache: {e}")

