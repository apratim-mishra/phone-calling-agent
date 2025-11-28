import io
import struct
from typing import Optional

import numpy as np
import soundfile as sf

from src.config import settings
from src.utils.errors import AudioError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# μ-law encoding/decoding tables
MULAW_BIAS = 0x84
MULAW_CLIP = 32635


class AudioProcessor:
    """Audio format conversion for telephony (mu-law, PCM16)."""

    def __init__(
        self,
        sample_rate: int = settings.audio_sample_rate,
        channels: int = settings.audio_channels,
    ):
        self.sample_rate = sample_rate
        self.channels = channels

    def mulaw_to_pcm16(self, mulaw_data: bytes) -> np.ndarray:
        """Convert mu-law encoded audio to PCM16 numpy array."""
        try:
            pcm_samples = []
            for byte in mulaw_data:
                byte = ~byte
                sign = (byte & 0x80) >> 7
                exponent = (byte & 0x70) >> 4
                mantissa = byte & 0x0F

                sample = (mantissa << 3) + MULAW_BIAS
                sample <<= exponent
                sample -= MULAW_BIAS

                if sign:
                    sample = -sample

                pcm_samples.append(sample)

            return np.array(pcm_samples, dtype=np.int16)
        except Exception as e:
            raise AudioError(f"Failed to convert mu-law to PCM16: {e}")

    def pcm16_to_mulaw(self, pcm_data: np.ndarray) -> bytes:
        """Convert PCM16 numpy array to mu-law encoded bytes."""
        try:
            mulaw_bytes = []
            for sample in pcm_data:
                sample = int(sample)
                sign = 0

                if sample < 0:
                    sign = 0x80
                    sample = -sample

                sample = min(sample, MULAW_CLIP)
                sample += MULAW_BIAS

                exponent = 7
                exp_mask = 0x4000
                while exponent > 0 and (sample & exp_mask) == 0:
                    exponent -= 1
                    exp_mask >>= 1

                mantissa = (sample >> (exponent + 3)) & 0x0F
                mulaw_byte = ~(sign | (exponent << 4) | mantissa) & 0xFF
                mulaw_bytes.append(mulaw_byte)

            return bytes(mulaw_bytes)
        except Exception as e:
            raise AudioError(f"Failed to convert PCM16 to mu-law: {e}")

    def bytes_to_float32(self, audio_bytes: bytes) -> np.ndarray:
        """Convert raw PCM16 bytes to float32 numpy array for model input."""
        try:
            pcm16 = np.frombuffer(audio_bytes, dtype=np.int16)
            return pcm16.astype(np.float32) / 32768.0
        except Exception as e:
            raise AudioError(f"Failed to convert bytes to float32: {e}")

    def float32_to_bytes(self, audio: np.ndarray) -> bytes:
        """Convert float32 numpy array to PCM16 bytes."""
        try:
            pcm16 = (audio * 32767).astype(np.int16)
            return pcm16.tobytes()
        except Exception as e:
            raise AudioError(f"Failed to convert float32 to bytes: {e}")

    def resample(
        self, audio: np.ndarray, orig_sr: int, target_sr: Optional[int] = None
    ) -> np.ndarray:
        """Resample audio to target sample rate using linear interpolation."""
        if target_sr is None:
            target_sr = self.sample_rate

        if orig_sr == target_sr:
            return audio

        try:
            duration = len(audio) / orig_sr
            target_length = int(duration * target_sr)
            indices = np.linspace(0, len(audio) - 1, target_length)
            return np.interp(indices, np.arange(len(audio)), audio).astype(audio.dtype)
        except Exception as e:
            raise AudioError(f"Failed to resample audio: {e}")

    def to_wav_bytes(self, audio: np.ndarray, sample_rate: Optional[int] = None) -> bytes:
        """Convert numpy array to WAV format bytes."""
        try:
            sr = sample_rate or self.sample_rate
            buffer = io.BytesIO()
            sf.write(buffer, audio, sr, format="WAV", subtype="PCM_16")
            buffer.seek(0)
            return buffer.read()
        except Exception as e:
            raise AudioError(f"Failed to convert to WAV: {e}")

    def from_wav_bytes(self, wav_bytes: bytes) -> tuple[np.ndarray, int]:
        """Read WAV bytes and return numpy array with sample rate."""
        try:
            buffer = io.BytesIO(wav_bytes)
            audio, sample_rate = sf.read(buffer, dtype="float32")
            return audio, sample_rate
        except Exception as e:
            raise AudioError(f"Failed to read WAV bytes: {e}")

    def normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.abs(audio).max()
        if max_val > 0:
            return audio / max_val
        return audio

    def chunk_audio(self, audio: np.ndarray, chunk_duration_ms: int = 20) -> list[np.ndarray]:
        """Split audio into chunks for streaming."""
        chunk_size = int(self.sample_rate * chunk_duration_ms / 1000)
        return [audio[i : i + chunk_size] for i in range(0, len(audio), chunk_size)]

