"""
Configuration for the LLM client.
This module contains the configuration settings for connecting to the LLM API.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for the LLM API client."""
    
    # API endpoint
    api_host: str = "https://llm.chutes.ai/v1"
    
    # API authentication
    api_key: str = ""
    
    # Model configuration
    model_name: str = "chutesai/Llama-4-Scout-17B-16E-Instruct"
    
    # Request parameters
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create a configuration from environment variables."""
        return cls(
            api_host=os.environ.get("LLM_API_HOST", "https://llm.chutes.ai/v1"),
            api_key=os.environ.get("LLM_API_KEY", ""),
            model_name=os.environ.get("LLM_MODEL_NAME", "chutesai/Llama-4-Scout-17B-16E-Instruct"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "1024")),
            top_p=float(os.environ.get("LLM_TOP_P", "0.9")),
            frequency_penalty=float(os.environ.get("LLM_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.environ.get("LLM_PRESENCE_PENALTY", "0.0")),
        )
