"""
LLM module for interacting with the custom LLM API.
This module provides client functionality for connecting to and querying the LLM API.
"""

from .client import LLMClient
from .config import LLMConfig

__all__ = ["LLMClient", "LLMConfig"]
