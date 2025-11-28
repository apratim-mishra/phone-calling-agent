from typing import Optional

import numpy as np

from src.config import settings
from src.utils.errors import TranscriptionError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WhisperSTT:
    """Speech-to-text using MLX Whisper."""

    def __init__(self, model_size: Optional[str] = None):
        self.model_size = model_size or settings.whisper_model_size
        self._model = None
        self._processor = None

    def _load_model(self) -> None:
        """Lazy load the Whisper model."""
        if self._model is not None:
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
            logger.debug(f"Transcription: {text[:100]}...")
            return text

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}", {"model": self.model_size})

    async def transcribe_async(
        self,
        audio: np.ndarray,
        language: str = "en",
        sample_rate: int = 16000,
    ) -> str:
        """Async wrapper for transcription."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.transcribe(audio, language, sample_rate)
        )

    def clear_cache(self) -> None:
        """Clear MLX cache to free memory."""
        try:
            import mlx.core as mx

            mx.clear_cache()
            logger.debug("MLX cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear MLX cache: {e}")

