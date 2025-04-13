"""
Tests for the LLM client module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from src.llm.client import LLMClient
from src.llm.config import LLMConfig


class TestLLMClient(unittest.TestCase):
    """Tests for the LLM client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            api_host="https://llm.chutes.ai/v1",
            api_key="test_api_key",
            model_name="chutesai/Llama-4-Scout-17B-16E-Instruct",
        )
        self.client = LLMClient(self.config)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.client.config.api_host, "https://llm.chutes.ai/v1")
        self.assertEqual(self.client.config.api_key, "test_api_key")
        self.assertEqual(self.client.config.model_name, "chutesai/Llama-4-Scout-17B-16E-Instruct")
    
    def test_get_headers(self):
        """Test getting headers."""
        headers = self.client._get_headers()
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Authorization"], "Bearer test_api_key")
    
    @patch("src.llm.client.requests.post")
    def test_generate_completion(self, mock_post):
        """Test generating a completion."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"text": "Test response"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Call the method
        response = self.client.generate_completion("Test prompt")
        
        # Check the response
        self.assertEqual(response["choices"][0]["text"], "Test response")
        
        # Check the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["prompt"], "Test prompt")
        self.assertEqual(kwargs["json"]["model"], "chutesai/Llama-4-Scout-17B-16E-Instruct")
    
    @patch("src.llm.client.requests.post")
    def test_generate_text(self, mock_post):
        """Test generating text."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"text": "Test response"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Call the method
        response = self.client.generate_text("Test prompt")
        
        # Check the response
        self.assertEqual(response, "Test response")
    
    @patch("src.llm.client.requests.post")
    def test_error_handling(self, mock_post):
        """Test error handling."""
        # Mock error response
        mock_post.side_effect = Exception("Test error")
        
        # Call the method and check for exception
        with self.assertRaises(Exception):
            self.client.generate_completion("Test prompt")


if __name__ == "__main__":
    unittest.main()
