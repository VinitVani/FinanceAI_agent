import pytest
from unittest.mock import patch, MagicMock
from Backend.agent.example_agent import run_example_agent
from Backend.core.llm_client import LLMError

def test_run_example_agent_success(capsys):
    """Test successful run of example agent."""
    with patch("Backend.agent.example_agent.get_llm_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate.return_value = "Hello user!"
        mock_get_client.return_value = mock_client
        
        run_example_agent()
        
        captured = capsys.readouterr()
        assert "Initializing Example Agent..." in captured.out
        assert "Agent Response: Hello user!" in captured.out

def test_run_example_agent_llm_error(capsys):
    """Test handling of LLMError."""
    with patch("Backend.agent.example_agent.get_llm_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate.side_effect = LLMError("API failure")
        mock_get_client.return_value = mock_client
        
        run_example_agent()
        
        captured = capsys.readouterr()
        assert "Agent failed: API failure" in captured.out

def test_run_example_agent_unexpected_error(capsys):
    """Test handling of unexpected exceptions."""
    with patch("Backend.agent.example_agent.get_llm_client") as mock_get_client:
        mock_get_client.side_effect = Exception("Boom")
        
        run_example_agent()
        
        captured = capsys.readouterr()
        assert "Unexpected error: Boom" in captured.out
