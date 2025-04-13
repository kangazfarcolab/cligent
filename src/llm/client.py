"""
LLM client for interacting with the custom LLM API.
This module provides a client for sending requests to and receiving responses from the LLM API.
"""

import json
import logging
from typing import Dict, List, Optional, Union, Any

import requests

from .config import LLMConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with the LLM API."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM client with the given configuration.

        Args:
            config: Configuration for the LLM API. If None, loads from environment.
        """
        self.config = config or LLMConfig.from_env()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the configuration."""
        if not self.config.api_key:
            raise ValueError("API key is required")
        if not self.config.api_host:
            raise ValueError("API host is required")
        if not self.config.model_name:
            raise ValueError("Model name is required")

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for the API request."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "x-api-key": self.config.api_key  # Adding alternative auth header format
        }

    def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
    ) -> str:
        """Generate text from the LLM based on the prompt.

        Args:
            prompt: The prompt to send to the LLM.
            temperature: Controls randomness. Higher values mean more random completions.
            max_tokens: Maximum number of tokens to generate.
            top_p: Controls diversity via nucleus sampling.
            frequency_penalty: Penalizes repeated tokens.
            presence_penalty: Penalizes repeated topics.

        Returns:
            The generated text response.
        """
        response = self.generate_completion(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )

        # Extract the text from the response
        # This may need to be adjusted based on the actual API response format
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")

    def generate_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send a completion request to the LLM API.

        Args:
            prompt: The prompt to send to the LLM.
            temperature: Controls randomness. Higher values mean more random completions.
            max_tokens: Maximum number of tokens to generate.
            top_p: Controls diversity via nucleus sampling.
            frequency_penalty: Penalizes repeated tokens.
            presence_penalty: Penalizes repeated topics.

        Returns:
            The raw API response as a dictionary.
        """
        url = f"{self.config.api_host}/chat/completions"

        # Prepare the request payload
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            "top_p": top_p if top_p is not None else self.config.top_p,
            "frequency_penalty": frequency_penalty if frequency_penalty is not None else self.config.frequency_penalty,
            "presence_penalty": presence_penalty if presence_penalty is not None else self.config.presence_penalty,
        }

        # Log the request for debugging
        logger.debug(f"Sending request to {url}")
        logger.debug(f"Headers: {self._get_headers()}")
        logger.debug(f"Payload: {payload}")

        # Send the request
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=60,  # 60 second timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            raise
