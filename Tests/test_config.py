import pytest

from Backend.core.config import LLMProvider, Settings, get_settings


def test_settings_defaults():
    """Test that default settings are correct."""
    settings = Settings(
        # We must provide keys for validators to pass if defaults are missing in env
        # But here we mock env vars or provide minimal valid config
        OPENAI_API_KEY="test-key",
        ANTHROPIC_API_KEY="test-key",
        LOCAL_MODEL_ENDPOINT="http://localhost:8000",
    )
    assert settings.LLM_PROVIDER == LLMProvider.OPENAI
    assert settings.ENVIRONMENT == "development"
    assert settings.MAX_TOKENS == 2048


def test_missing_openai_key():
    """Test that missing OpenAI key raises error when provider is OpenAI."""
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        Settings(LLM_PROVIDER=LLMProvider.OPENAI, OPENAI_API_KEY=None)


def test_missing_anthropic_key():
    """Test that missing Anthropic key raises error when provider is Anthropic."""
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
        Settings(LLM_PROVIDER=LLMProvider.ANTHROPIC, ANTHROPIC_API_KEY=None)


def test_valid_config():
    """Test a valid configuration."""
    settings = Settings(
        LLM_PROVIDER=LLMProvider.OPENAI, OPENAI_API_KEY="sk-test", MAX_TOKENS=1000
    )
    assert settings.OPENAI_API_KEY == "sk-test"
    assert settings.MAX_TOKENS == 1000


def test_get_settings_singleton(monkeypatch):
    """Test that get_settings returns the same instance."""
    # Ensure invalid config doesn't crash this test by providing valid envs
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
