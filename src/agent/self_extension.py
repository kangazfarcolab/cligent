"""
Self-extension module for enabling the agent to create new capabilities.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Set, Tuple

from ..llm.client import LLMClient
from ..plugins.base import PluginManager
from ..plugins.meta_manager import MetaPluginManager
from ..mcp.base import MCPManager
from ..mcp.generator import MCPTemplateGenerator
from ..generation.code_generator import CodeGenerator
from .task_analyzer import TaskAnalyzer
from .capability_manager import CapabilityManager

logger = logging.getLogger(__name__)

class SelfExtensionManager:
    """Manager for self-extension capabilities."""

    def __init__(
        self,
        llm_client: LLMClient,
        plugin_manager: PluginManager,
        mcp_manager: MCPManager,
        require_confirmation: bool = True
    ):
        """Initialize the self-extension manager.

        Args:
            llm_client: LLM client for generating capabilities.
            plugin_manager: Plugin manager for accessing plugins.
            mcp_manager: MCP manager for accessing templates.
            require_confirmation: Whether to require user confirmation for extensions.
        """
        self.llm_client = llm_client
        self.plugin_manager = plugin_manager
        self.mcp_manager = mcp_manager
        self.require_confirmation = require_confirmation

        # Create component instances
        self.meta_plugin_manager = MetaPluginManager(
            llm_client=llm_client,
            plugin_manager=plugin_manager
        )

        self.mcp_generator = MCPTemplateGenerator(
            llm_client=llm_client,
            mcp_manager=mcp_manager
        )

        self.code_generator = CodeGenerator(
            llm_client=llm_client
        )

        self.task_analyzer = TaskAnalyzer(
            llm_client=llm_client
        )

        self.capability_manager = CapabilityManager(
            llm_client=llm_client,
            plugin_manager=plugin_manager,
            meta_plugin_manager=self.meta_plugin_manager,
            mcp_manager=mcp_manager,
            mcp_generator=self.mcp_generator,
            code_generator=self.code_generator
        )

        # Create necessary directories for self-extension
        self._ensure_directories_exist()

    def analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze a user request to identify required capabilities.

        Args:
            request: The user request to analyze.

        Returns:
            Analysis of the request, including subtasks and missing capabilities.
        """
        # Get current capabilities
        current_capabilities = self.capability_manager.get_available_capabilities()

        # Analyze the request
        return self.task_analyzer.analyze_request(request, current_capabilities)

    def handle_request(
        self,
        request: str,
        user_confirmation_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Handle a user request, creating capabilities if needed.

        Args:
            request: The user request to handle.
            user_confirmation_callback: Callback for getting user confirmation.

        Returns:
            Result of handling the request.
        """
        logger.info(f"Handling request: {request}")

        # Analyze the request
        analysis = self.analyze_request(request)

        if "error" in analysis:
            return {"error": f"Request analysis failed: {analysis['error']}"}

        # Check if there are missing capabilities
        missing_capabilities = analysis.get("missing_capabilities", [])

        if not missing_capabilities:
            return {
                "success": True,
                "message": "No new capabilities needed to handle this request",
                "analysis": analysis
            }

        # Create missing capabilities
        created_capabilities = []
        for capability in missing_capabilities:
            # Get user confirmation if required
            if self.require_confirmation and user_confirmation_callback:
                confirm = user_confirmation_callback(
                    f"Create new capability: {capability['name']} ({capability['type']})"
                )
                if not confirm:
                    logger.info(f"User declined to create capability: {capability['name']}")
                    continue

            # Create the capability
            result = self.capability_manager.create_capability(
                capability_type=capability["type"],
                name=capability["name"],
                description=capability["description"],
                details=capability.get("details", {})
            )

            if "error" in result:
                logger.error(f"Failed to create capability {capability['name']}: {result['error']}")
                continue

            created_capabilities.append(result)
            logger.info(f"Created capability: {capability['name']} ({capability['type']})")

        return {
            "success": True,
            "message": f"Created {len(created_capabilities)} new capabilities",
            "analysis": analysis,
            "created_capabilities": created_capabilities
        }

    def create_mcp_template(
        self,
        task: str,
        description: str,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """Create an MCP template.

        Args:
            task: The task for which to create a template.
            description: Detailed description of the task.
            additional_context: Any additional context or requirements.

        Returns:
            Result of the template creation.
        """
        template = self.mcp_generator.generate_template(
            task=task,
            description=description,
            additional_context=additional_context
        )

        if not template:
            return {"error": "Failed to generate MCP template"}

        return {
            "success": True,
            "template": template.to_dict()
        }

    def create_plugin(
        self,
        name: str,
        description: str,
        capabilities: str,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """Create a plugin.

        Args:
            name: The name of the plugin.
            description: Description of the plugin.
            capabilities: Description of the plugin's capabilities.
            additional_context: Any additional context or requirements.

        Returns:
            Result of the plugin creation.
        """
        plugin_file = self.meta_plugin_manager.generate_plugin(
            name=name,
            description=description,
            capabilities=capabilities,
            additional_context=additional_context
        )

        if not plugin_file:
            return {"error": "Failed to generate plugin"}

        return {
            "success": True,
            "plugin_file": plugin_file
        }

    def _ensure_directories_exist(self) -> None:
        """Ensure all necessary directories for self-extension exist."""
        # Create directories for plugins, templates, and Docker configurations
        directories = [
            "plugins",
            "templates/mcp",
            "templates/mcp/generated",
            "templates/plugins",
            "docker"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def create_docker_config(
        self,
        requirements: str,
        name: str,
        additional_context: str = "",
        file_type: str = "Dockerfile"
    ) -> Dict[str, Any]:
        """Create a Docker configuration.

        Args:
            requirements: Detailed requirements for the Docker configuration.
            name: Name for the Docker configuration.
            additional_context: Any additional context or requirements.
            file_type: Type of file to generate (Dockerfile, docker-compose.yml, etc.).

        Returns:
            Result of the Docker configuration creation.
        """
        # Ensure docker directory exists
        os.makedirs("docker", exist_ok=True)

        result = self.code_generator.generate_docker_config(
            requirements=requirements,
            additional_context=additional_context,
            file_type=file_type
        )

        if "error" in result:
            return {"error": f"Failed to generate Docker configuration: {result['error']}"}

        # Save the configuration
        file_path = f"docker/{name.lower().replace(' ', '_')}.{result['file_type'].lower()}"
        saved = self.code_generator.save_generated_code(
            code=result["configuration"],
            file_path=file_path,
            overwrite=False
        )

        if not saved:
            return {"error": f"Failed to save Docker configuration to {file_path}"}

        return {
            "success": True,
            "file": file_path,
            "configuration": result["configuration"],
            "explanation": result["explanation"]
        }
