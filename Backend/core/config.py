from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: LLMProvider = Field(
        default=LLMProvider.OPENAI, description="LLM provider to use"
    )

    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API Key")
    OPENAI_MODEL: str = Field("gpt-4o-mini", description="OpenAI Model")

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API Key")
    ANTHROPIC_MODEL: str = Field(
        "claude-3-5-sonnet-20241022", description="Anthropic Model"
    )

    # Local
    LOCAL_MODEL_ENDPOINT: Optional[str] = Field(
        None, description="Local model endpoint URL"
    )

    # Safety & Limits
    MAX_TOKENS: int = Field(2048, ge=1, le=32000, description="Max tokens per response")
    MAX_COST_PER_REQUEST: Optional[float] = Field(
        None, description="Max cost in USD per request"
    )

    # Environment
    ENVIRONMENT: str = Field(
        "development", description="Environment (development/production)"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @field_validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v, info):
        if info.data.get("LLM_PROVIDER") == LLMProvider.OPENAI and not v:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return v

    @field_validator("ANTHROPIC_API_KEY")
    def validate_anthropic_key(cls, v, info):
        if info.data.get("LLM_PROVIDER") == LLMProvider.ANTHROPIC and not v:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        return v

    @field_validator("LOCAL_MODEL_ENDPOINT")
    def validate_local_endpoint(cls, v, info):
        if info.data.get("LLM_PROVIDER") == LLMProvider.LOCAL and not v:
            raise ValueError("LOCAL_MODEL_ENDPOINT is required when LLM_PROVIDER=local")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the settings."""
    return Settings()
