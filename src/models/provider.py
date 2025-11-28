from typing import AsyncIterator, Optional
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from src.config import settings
from src.utils.errors import LLMError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LLMProvider:
    """LLM provider with Z.ai primary and OpenAI fallback."""

    def __init__(
        self,
        primary_api_key: Optional[str] = None,
        primary_base_url: Optional[str] = None,
        primary_model: Optional[str] = None,
        fallback_api_key: Optional[str] = None,
        fallback_model: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.7,
    ):
        self.primary_api_key = primary_api_key or settings.z_ai_api_key
        self.primary_base_url = primary_base_url or settings.z_ai_base_url
        self.primary_model = primary_model or settings.z_ai_model
        self.fallback_api_key = fallback_api_key or settings.openai_api_key
        self.fallback_model = fallback_model or settings.openai_model
        self.max_tokens = max_tokens
        self.temperature = temperature

        self._primary_client: Optional[ChatOpenAI] = None
        self._fallback_client: Optional[ChatOpenAI] = None

    def _get_primary_client(self) -> Optional[ChatOpenAI]:
        """Get the primary Z.ai client."""
        if not self.primary_api_key or not self.primary_model:
            return None

        if self._primary_client is None:
            self._primary_client = ChatOpenAI(
                api_key=self.primary_api_key,
                base_url=self.primary_base_url,
                model=self.primary_model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            logger.info(f"Initialized Z.ai client with model: {self.primary_model}")

        return self._primary_client

    def _get_fallback_client(self) -> Optional[ChatOpenAI]:
        """Get the fallback OpenAI client."""
        if not self.fallback_api_key:
            return None

        if self._fallback_client is None:
            self._fallback_client = ChatOpenAI(
                api_key=self.fallback_api_key,
                model=self.fallback_model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            logger.info(f"Initialized OpenAI fallback with model: {self.fallback_model}")

        return self._fallback_client

    def get_model(self) -> BaseChatModel:
        """Get the active LLM model (primary or fallback)."""
        primary = self._get_primary_client()
        if primary:
            return primary

        fallback = self._get_fallback_client()
        if fallback:
            logger.warning("Using fallback OpenAI model")
            return fallback

        raise LLMError("No LLM provider configured. Set Z_AI_API_KEY or OPENAI_API_KEY.")

    async def generate(
        self,
        messages: list[BaseMessage],
        use_fallback: bool = False,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            messages: List of chat messages
            use_fallback: Force use of fallback provider

        Returns:
            Generated text response
        """
        client = self._get_fallback_client() if use_fallback else None
        if client is None:
            client = self.get_model()

        try:
            response = await client.ainvoke(messages)
            return response.content
        except Exception as e:
            if not use_fallback and self._get_fallback_client():
                logger.warning(f"Primary LLM failed, trying fallback: {e}")
                return await self.generate(messages, use_fallback=True)
            raise LLMError(f"LLM generation failed: {e}")

    async def stream(
        self,
        messages: list[BaseMessage],
    ) -> AsyncIterator[str]:
        """Stream response tokens from the LLM.

        Args:
            messages: List of chat messages

        Yields:
            Response tokens as they're generated
        """
        client = self.get_model()

        try:
            async for chunk in client.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            raise LLMError(f"LLM streaming failed: {e}")


@lru_cache
def get_llm() -> LLMProvider:
    """Get singleton LLM provider instance."""
    return LLMProvider()

