"""
Pytest configuration file.
"""

import os
import pytest
from unittest.mock import patch

from src.llm.config import LLMConfig
from src.agent.state import AgentState


@pytest.fixture
def test_config():
    """Fixture for test LLM configuration."""
    return LLMConfig(
        api_host="https://llm.chutes.ai/v1",
        api_key="test_api_key",
        model_name="chutesai/Llama-4-Scout-17B-16E-Instruct",
    )


@pytest.fixture
def test_state():
    """Fixture for test agent state."""
    return AgentState(working_directory="/tmp")


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Fixture to mock environment variables."""
    monkeypatch.setenv("LLM_API_KEY", "test_api_key")
    monkeypatch.setenv("LLM_API_HOST", "https://llm.chutes.ai/v1")
    monkeypatch.setenv("LLM_MODEL_NAME", "chutesai/Llama-4-Scout-17B-16E-Instruct")
