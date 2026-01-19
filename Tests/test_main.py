from unittest.mock import MagicMock, patch

from Backend.core.config import LLMProvider
from Backend.main import main


def test_main_execution(capsys):
    """Test main function execution."""
    mock_settings = MagicMock()
    mock_settings.ENVIRONMENT = "test-env"
    mock_settings.LLM_PROVIDER = LLMProvider.OPENAI

    with patch("Backend.main.get_settings", return_value=mock_settings):
        main()

        captured = capsys.readouterr()
        assert "Starting FinanceAI Agent Backend..." in captured.out
        assert "Environment: test-env" in captured.out
        assert "LLM Provider: LLMProvider.OPENAI" in captured.out
        assert "Service initialized" in captured.out
