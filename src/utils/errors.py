from typing import Optional


class AgentError(Exception):
    """Base exception for phone agent errors."""

    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")


class TranscriptionError(AgentError):
    """E001: Speech-to-text transcription failed."""

    def __init__(self, message: str = "Transcription failed", details: Optional[dict] = None):
        super().__init__("E001", message, details)


class TTSError(AgentError):
    """E002: Text-to-speech generation failed."""

    def __init__(self, message: str = "TTS generation failed", details: Optional[dict] = None):
        super().__init__("E002", message, details)


class LLMError(AgentError):
    """E003: LLM request failed."""

    def __init__(self, message: str = "LLM request failed", details: Optional[dict] = None):
        super().__init__("E003", message, details)


class VectorSearchError(AgentError):
    """E004: Vector search failed."""

    def __init__(self, message: str = "Vector search failed", details: Optional[dict] = None):
        super().__init__("E004", message, details)


class TwilioError(AgentError):
    """E005: Twilio webhook validation failed."""

    def __init__(
        self, message: str = "Twilio webhook validation failed", details: Optional[dict] = None
    ):
        super().__init__("E005", message, details)


class AudioError(AgentError):
    """Audio processing error."""

    def __init__(self, message: str = "Audio processing failed", details: Optional[dict] = None):
        super().__init__("E006", message, details)

