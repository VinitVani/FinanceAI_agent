import pytest
from unittest.mock import MagicMock, patch
from Backend.core.llm_client import (
    LLMClient, 
    OpenAIClient, 
    AnthropicClient, 
    LocalClient, 
    LLMProvider, 
    LLMConfigurationError,
    LLMError
)
from Backend.core.config import Settings

@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to mock settings."""
    def _mock_settings(provider, openai_key=None, anthropic_key=None, local_endpoint=None):
        settings = MagicMock(spec=Settings)
        settings.LLM_PROVIDER = provider
        settings.OPENAI_API_KEY = openai_key
        settings.ANTHROPIC_API_KEY = anthropic_key
        settings.LOCAL_MODEL_ENDPOINT = local_endpoint
        settings.OPENAI_MODEL = "gpt-model"
        settings.ANTHROPIC_MODEL = "claude-model"
        settings.MAX_TOKENS = 100
        
        # Patch get_settings to return our mock
        monkeypatch.setattr("Backend.core.llm_client.get_settings", lambda: settings)
        monkeypatch.setattr("Backend.core.config.get_settings", lambda: settings)
        return settings
    return _mock_settings

class TestOpenAIClient:
    def test_init_raises_if_no_key(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key=None)
        with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY is required"):
            OpenAIClient()

    def test_init_success(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key="sk-test")
        with patch("openai.OpenAI"):
            client = OpenAIClient()
            assert client.model == "gpt-model"

    def test_generate_success(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key="sk-test")
        with patch("openai.OpenAI") as MockOpenAI:
             mock_instance = MockOpenAI.return_value
             mock_completion = MagicMock()
             mock_completion.choices[0].message.content = "test response"
             mock_instance.chat.completions.create.return_value = mock_completion
             
             client = OpenAIClient()
             response = client.generate("hello")
             assert response == "test response"

    def test_generate_failure(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key="sk-test")
        with patch("openai.OpenAI") as MockOpenAI:
            mock_instance = MockOpenAI.return_value
            mock_instance.chat.completions.create.side_effect = Exception("API Error")
            
            client = OpenAIClient()
            with pytest.raises(LLMError, match="OpenAI generation failed"):
                client.generate("hello")

class TestAnthropicClient:
    def test_init_raises_if_no_key(self, mock_settings):
        mock_settings(LLMProvider.ANTHROPIC, anthropic_key=None)
        with pytest.raises(LLMConfigurationError, match="ANTHROPIC_API_KEY is required"):
            AnthropicClient()

    def test_generate_success(self, mock_settings):
        mock_settings(LLMProvider.ANTHROPIC, anthropic_key="sk-ant")
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_instance = MockAnthropic.return_value
            mock_msg = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "claude response"
            mock_msg.content = [mock_content]
            mock_instance.messages.create.return_value = mock_msg
            
            client = AnthropicClient()
            response = client.generate("hello")
            assert response == "claude response"

class TestLocalClient:
    def test_init_raises_if_no_endpoint(self, mock_settings):
        mock_settings(LLMProvider.LOCAL, local_endpoint=None)
        with pytest.raises(LLMConfigurationError, match="LOCAL_MODEL_ENDPOINT is required"):
            LocalClient()

    def test_generate_success(self, mock_settings):
        mock_settings(LLMProvider.LOCAL, local_endpoint="http://local")
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"choices": [{"message": {"content": "local response"}}]}
            mock_post.return_value = mock_resp
            
            client = LocalClient()
            response = client.generate("hello")
            assert response == "local response"

class TestLLMClientWrapper:
    def test_delegates_to_provider(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key="sk-test")
        with patch("openai.OpenAI"):
            client = LLMClient()
            assert isinstance(client._delegate, OpenAIClient)

    def test_factory_function(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key="sk-test")
        with patch("openai.OpenAI"):
            from Backend.core.llm_client import get_llm_client
            client = get_llm_client()
            assert isinstance(client, LLMClient)

    def test_import_error_openai(self, mock_settings):
        mock_settings(LLMProvider.OPENAI, openai_key="sk-test")
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(LLMError, match="openai package is not installed"):
                OpenAIClient()

    def test_import_error_anthropic(self, mock_settings):
        mock_settings(LLMProvider.ANTHROPIC, anthropic_key="sk-ant")
        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(LLMError, match="anthropic package is not installed"):
                AnthropicClient()
