import logging
from abc import ABC, abstractmethod
from typing import Optional

# Import settings but don't instantiate immediately to avoid import loops if any
from .config import LLMProvider, get_settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class LLMConfigurationError(LLMError):
    """Raised when LLM is misconfigured."""

    pass


class LLMClientInterface(ABC):
    """Abstract interface for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from LLM."""
        pass


class OpenAIClient(LLMClientInterface):
    """OpenAI implementation."""

    def __init__(self):
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise LLMConfigurationError(
                "OPENAI_API_KEY is required but not set. "
                "Please set it in your environment variables."
            )
        try:
            import openai

            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        except ImportError:
            raise LLMError("openai package is not installed.")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=get_settings().MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(f"OpenAI generation failed: {str(e)}") from e


class AnthropicClient(LLMClientInterface):
    """Anthropic implementation."""

    def __init__(self):
        settings = get_settings()
        if not settings.ANTHROPIC_API_KEY:
            raise LLMConfigurationError(
                "ANTHROPIC_API_KEY is required but not set. "
                "Please set it in your environment variables."
            )
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.ANTHROPIC_MODEL
        except ImportError:
            raise LLMError("anthropic package is not installed.")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            # Note: Anthropic system prompt is a top-level parameter in newer APIs
            response = self.client.messages.create(
                model=self.model,
                max_tokens=get_settings().MAX_TOKENS,
                system=system_prompt if system_prompt else "",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            raise LLMError(f"Anthropic generation failed: {str(e)}") from e


class LocalClient(LLMClientInterface):
    """Local LLM implementation (OpenAI-compatible endpoint)."""

    def __init__(self):
        settings = get_settings()
        if not settings.LOCAL_MODEL_ENDPOINT:
            raise LLMConfigurationError(
                "LOCAL_MODEL_ENDPOINT is required when LLM_PROVIDER=local"
            )
        # Using requests or openai client with custom base_url
        self.endpoint = settings.LOCAL_MODEL_ENDPOINT

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Simplified stub for local provider
        # In a real impl, might use `requests` or `openai` SDK with base_url
        import requests

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": get_settings().MAX_TOKENS,
        }

        try:
            resp = requests.post(self.endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMError(f"Local LLM generation failed: {str(e)}") from e


class LLMClient(LLMClientInterface):
    """Unified client that routes to the configured provider."""

    def __init__(self):
        settings = get_settings()
        self.provider = settings.LLM_PROVIDER
        self._delegate = self._get_client()

    def _get_client(self) -> LLMClientInterface:
        # self.provider is already set in __init__ using settings.LLM_PROVIDER.
        if self.provider == LLMProvider.OPENAI:
            return OpenAIClient()
        elif self.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient()
        elif self.provider == LLMProvider.LOCAL:
            return LocalClient()
        else:
            raise LLMConfigurationError(
                f"Unknown LLM provider: {self.provider}. "
                f"Supported providers: {', '.join([p.value for p in LLMProvider])}"
            )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # TODO: Add cost calculation logic using get_settings().MAX_COST_PER_REQUEST
        return self._delegate.generate(prompt, system_prompt)


def get_llm_client() -> LLMClient:
    """Factory function to get LLMClient instance."""
    return LLMClient()
