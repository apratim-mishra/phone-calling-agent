from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "realtime-phone-agent"
    app_port: int = 8000
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # LLM - Z.ai (primary)
    z_ai_api_key: str = ""
    z_ai_base_url: str = "https://api.z.ai/api/paas/v4/"
    z_ai_model: str = ""

    # LLM - Groq (fast inference - recommended for phone calls)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-70b-versatile"  # Fast & capable

    # LLM - OpenAI (fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # STT Provider: "local" (MLX Whisper) or "groq" (Groq Whisper API)
    stt_provider: Literal["local", "groq"] = "local"

    # MLX Models
    whisper_model_size: Literal["tiny", "base", "small","medium", "large-v3"] = "base"
    tts_model: str = "kokoro-v0_19"
    tts_voice: str = "af_sarah"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "properties"
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536

    # Weights & Biases
    wandb_api_key: str = ""
    wandb_project: str = "phone-agents"
    wandb_enabled: bool = False

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Audio Settings
    audio_sample_rate: int = 16000
    audio_channels: int = 1

    @property
    def primary_llm_available(self) -> bool:
        return bool(self.z_ai_api_key and self.z_ai_model)

    @property
    def groq_llm_available(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def fallback_llm_available(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

