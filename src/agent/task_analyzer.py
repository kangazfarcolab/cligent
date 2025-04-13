"""
Task analyzer for breaking down user requests into required capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple

from ..llm.client import LLMClient
from ..mcp.processor import MCPProcessor
from ..mcp.base import MCPTemplate

logger = logging.getLogger(__name__)

class TaskAnalyzer:
    """Analyzer for breaking down user requests into required capabilities."""

    # Template for analyzing tasks
    TASK_ANALYSIS_TEMPLATE = {
        "name": "task_analyzer",
        "description": "Analyze a task to identify required capabilities",
        "version": "1.0",
        "prompt_template": """You are an expert at analyzing tasks and identifying the capabilities needed to complete them.
Analyze the following user request and identify the capabilities needed:

User Request: {request}

Current Capabilities:
{current_capabilities}

Your analysis should:
1. Break down the request into subtasks
2. Identify the capabilities needed for each subtask
3. Determine if any capabilities are missing
4. Suggest what new capabilities might need to be created

IMPORTANT: For simple questions or general conversation, DO NOT suggest creating new capabilities. Only suggest new capabilities for complex tasks that truly require them.

For example:
- "What is a car?" - This is a simple question that doesn't need new capabilities
- "Write a Python script to analyze stock market data" - This might need new capabilities

Provide a detailed analysis of the request and the capabilities needed.
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "The user request to analyze"
                },
                "current_capabilities": {
                    "type": "string",
                    "description": "List of currently available capabilities"
                }
            },
            "required": ["request", "current_capabilities"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "subtasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "required_capabilities": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "missing_capabilities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "type": {"type": "string", "enum": ["plugin", "mcp_template", "docker"]}
                        }
                    }
                },
                "summary": {"type": "string"}
            },
            "required": ["subtasks", "missing_capabilities", "summary"]
        }
    }

    def __init__(self, llm_client: LLMClient):
        """Initialize the task analyzer.

        Args:
            llm_client: LLM client for analyzing tasks.
        """
        self.llm_client = llm_client
        self.analysis_template = MCPTemplate.from_dict(self.TASK_ANALYSIS_TEMPLATE)
        self.processor = MCPProcessor(llm_client)

    def analyze_request(
        self,
        request: str,
        current_capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a user request to identify required capabilities.

        Args:
            request: The user request to analyze.
            current_capabilities: Dictionary of currently available capabilities.

        Returns:
            Analysis of the request, including subtasks and missing capabilities.
        """
        logger.info(f"Analyzing request: {request}")

        # Format current capabilities as a string
        capabilities_str = ""
        for category, caps in current_capabilities.items():
            capabilities_str += f"{category}:\n"
            for name, desc in caps.items():
                capabilities_str += f"- {name}: {desc}\n"
            capabilities_str += "\n"

        # Prepare input for the analysis template
        input_data = {
            "request": request,
            "current_capabilities": capabilities_str
        }

        # Process the template
        result = self.processor.process(self.analysis_template, input_data)

        if "error" in result:
            logger.error(f"Task analysis failed: {result['error']}")
            return {"error": result["error"]}

        return result

    def identify_capability_gaps(
        self,
        required_capabilities: Set[str],
        available_capabilities: Dict[str, Any]
    ) -> List[str]:
        """Identify missing capabilities.

        Args:
            required_capabilities: Set of required capability names.
            available_capabilities: Dictionary of available capabilities.

        Returns:
            List of missing capability names.
        """
        # Flatten available capabilities
        available_flat = set()
        for category, caps in available_capabilities.items():
            available_flat.update(caps.keys())

        # Find missing capabilities
        return list(required_capabilities - available_flat)

    def extract_required_capabilities(
        self,
        analysis: Dict[str, Any]
    ) -> Set[str]:
        """Extract required capabilities from an analysis.

        Args:
            analysis: Analysis result from analyze_request.

        Returns:
            Set of required capability names.
        """
        required = set()

        for subtask in analysis.get("subtasks", []):
            required.update(subtask.get("required_capabilities", []))

        return required
