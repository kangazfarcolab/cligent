"""
Meta-plugin manager for dynamically generating and registering plugins.
"""

import os
import re
import json
import logging
import importlib.util
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

from ..llm.client import LLMClient
from .base import Plugin, PluginManager
from ..mcp.processor import MCPProcessor
from ..mcp.base import MCPTemplate

logger = logging.getLogger(__name__)

class PluginTemplate:
    """Template for generating plugins."""
    
    def __init__(
        self,
        name: str,
        description: str,
        template_code: str,
        capabilities: List[str]
    ):
        """Initialize a plugin template.
        
        Args:
            name: Name of the template.
            description: Description of the template.
            template_code: Template code for the plugin.
            capabilities: List of capabilities provided by the template.
        """
        self.name = name
        self.description = description
        self.template_code = template_code
        self.capabilities = capabilities
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary.
        
        Returns:
            Dictionary representation of the template.
        """
        return {
            "name": self.name,
            "description": self.description,
            "template_code": self.template_code,
            "capabilities": self.capabilities
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginTemplate':
        """Create a template from a dictionary.
        
        Args:
            data: Dictionary representation of the template.
            
        Returns:
            A PluginTemplate instance.
        """
        return cls(
            name=data["name"],
            description=data["description"],
            template_code=data["template_code"],
            capabilities=data["capabilities"]
        )
        
    @classmethod
    def from_json(cls, json_str: str) -> 'PluginTemplate':
        """Create a template from a JSON string.
        
        Args:
            json_str: JSON string representation of the template.
            
        Returns:
            A PluginTemplate instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    def to_json(self) -> str:
        """Convert the template to a JSON string.
        
        Returns:
            JSON string representation of the template.
        """
        return json.dumps(self.to_dict(), indent=2)

class MetaPluginManager:
    """Manager for dynamically generating and registering plugins."""

    # Template for generating plugin generator MCP
    META_PLUGIN_TEMPLATE = {
        "name": "plugin_generator",
        "description": "Generate a plugin based on requirements",
        "version": "1.0",
        "prompt_template": "You are an expert Python developer specializing in creating plugins for a CLI agent.\nCreate a plugin for the following requirements:\n\nPlugin Name: {name}\nDescription: {description}\nCapabilities:\n{capabilities}\n\nAdditional Context:\n{additional_context}\n\nThe plugin should:\n1. Inherit from the Plugin base class\n2. Implement all required methods (name, description, version, get_capabilities, execute)\n3. Include proper error handling\n4. Be well-documented with docstrings\n5. Follow PEP 8 style guidelines\n\nHere's the Plugin base class definition for reference:\n\n```python\nclass Plugin(ABC):\n    @property\n    @abstractmethod\n    def name(self) -> str:\n        \"\"\"Get the name of the plugin.\"\"\"\n        pass\n\n    @property\n    @abstractmethod\n    def description(self) -> str:\n        \"\"\"Get the description of the plugin.\"\"\"\n        pass\n\n    @property\n    @abstractmethod\n    def version(self) -> str:\n        \"\"\"Get the version of the plugin.\"\"\"\n        pass\n\n    @abstractmethod\n    def get_capabilities(self) -> Dict[str, Any]:\n        \"\"\"Get the capabilities of this plugin.\"\"\"\n        pass\n\n    @abstractmethod\n    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Execute a command with this plugin.\"\"\"\n        pass\n```\n\nProvide the complete plugin code as a Python file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the plugin"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the plugin"
                },
                "capabilities": {
                    "type": "string",
                    "description": "Description of the plugin's capabilities"
                },
                "additional_context": {
                    "type": "string",
                    "description": "Any additional context or requirements"
                }
            },
            "required": ["name", "description", "capabilities"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "plugin_code": {
                    "type": "string",
                    "description": "The generated plugin code"
                },
                "explanation": {
                    "type": "string",
                    "description": "Explanation of how the plugin works"
                },
                "imports": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of imports required by the plugin"
                }
            },
            "required": ["plugin_code", "explanation"]
        }
    }
    
    def __init__(
        self, 
        llm_client: LLMClient,
        plugin_manager: PluginManager,
        plugins_dir: str = "plugins",
        templates_dir: str = "templates/plugins"
    ):
        """Initialize the meta-plugin manager.
        
        Args:
            llm_client: LLM client for generating plugins.
            plugin_manager: Plugin manager for registering plugins.
            plugins_dir: Directory for storing generated plugins.
            templates_dir: Directory for plugin templates.
        """
        self.llm_client = llm_client
        self.plugin_manager = plugin_manager
        self.plugins_dir = plugins_dir
        self.templates_dir = templates_dir
        
        # Ensure required directories exist
        self._ensure_directories_exist()
        
        # Create the meta-template
        self.meta_template = MCPTemplate.from_dict(self.META_PLUGIN_TEMPLATE)
        self.processor = MCPProcessor(llm_client)
        
        # Load plugin templates
        self.plugin_templates: Dict[str, PluginTemplate] = {}
        self._load_plugin_templates()
        
    def _ensure_directories_exist(self) -> None:
        """Ensure all necessary directories exist."""
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        logger.info(f"Ensured directories exist: {self.plugins_dir}, {self.templates_dir}")
            
    def _load_plugin_templates(self) -> None:
        """Load plugin templates from the templates directory."""
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)

        for filename in os.listdir(self.templates_dir):
            if not filename.endswith(".json"):
                continue
                
            template_path = os.path.join(self.templates_dir, filename)
            try:
                with open(template_path, "r") as f:
                    template_data = json.load(f)
                    
                template = PluginTemplate.from_dict(template_data)
                self.plugin_templates[template.name] = template
                logger.info(f"Loaded plugin template: {template.name}")
            except Exception as e:
                logger.error(f"Error loading template from {template_path}: {e}")
                
    def save_template(self, template: PluginTemplate) -> bool:
        """Save a template to disk.
        
        Args:
            template: The template to save.
            
        Returns:
            True if the template was saved successfully, False otherwise.
        """
        os.makedirs(self.templates_dir, exist_ok=True)
        
        template_path = os.path.join(self.templates_dir, f"{template.name}.json")
        try:
            with open(template_path, "w") as f:
                json.dump(template.to_dict(), f, indent=2)
                
            logger.info(f"Saved template to {template_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving template to {template_path}: {e}")
            return False
            
    def generate_plugin(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """Generate a plugin based on requirements.
        
        Args:
            name: Name of the plugin.
            description: Description of the plugin.
            capabilities: List of capabilities provided by the plugin.
            additional_context: Any additional context or requirements.
            
        Returns:
            Dictionary with the generated plugin code and explanation.
        """
        logger.info(f"Generating plugin: {name}")
        
        # Format capabilities as a bulleted list
        capabilities_str = "\n".join([f"- {cap}" for cap in capabilities])
        
        # Prepare input for the meta-template
        input_data = {
            "name": name,
            "description": description,
            "capabilities": capabilities_str,
            "additional_context": additional_context
        }
        
        # Process the template
        result = self.processor.process(self.meta_template, input_data)
        
        if "error" in result:
            logger.error(f"Plugin generation failed: {result['error']}")
            return {"error": result["error"]}
            
        return result
        
    def save_plugin(self, name: str, code: str) -> Dict[str, Any]:
        """Save a generated plugin to disk.
        
        Args:
            name: Name of the plugin.
            code: The plugin code.
            
        Returns:
            Dictionary with the result of the save operation.
        """
        # Create a valid filename from the plugin name
        filename = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        if not filename.endswith(".py"):
            filename += ".py"
            
        # Create the plugins directory if it doesn't exist
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # Save the plugin code
        plugin_file = os.path.join(self.plugins_dir, filename)
        try:
            with open(plugin_file, "w") as f:
                f.write(code)
                
            logger.info(f"Saved plugin to {plugin_file}")
            return {
                "success": True,
                "file": plugin_file
            }
        except Exception as e:
            logger.error(f"Error saving plugin to {plugin_file}: {e}")
            return {
                "error": f"Failed to save plugin: {str(e)}"
            }
            
    def load_plugin(self, plugin_file: str) -> Dict[str, Any]:
        """Load a plugin from a file.
        
        Args:
            plugin_file: Path to the plugin file.
            
        Returns:
            Dictionary with the result of the load operation.
        """
        try:
            # Get the module name from the file path
            module_name = os.path.splitext(os.path.basename(plugin_file))[0]
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                return {"error": f"Failed to load plugin spec from {plugin_file}"}
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr.__module__ == module.__name__ and 
                    issubclass(attr, Plugin) and 
                    attr != Plugin):
                    plugin_class = attr
                    break
                    
            if plugin_class is None:
                return {"error": f"No plugin class found in {plugin_file}"}
                
            # Create an instance of the plugin
            plugin = plugin_class()
            
            # Register the plugin
            self.plugin_manager.register_plugin(plugin)
            
            logger.info(f"Loaded and registered plugin: {plugin.name}")
            return {
                "success": True,
                "plugin": plugin.name,
                "description": plugin.description,
                "capabilities": plugin.get_capabilities()
            }
        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_file}: {e}")
            return {
                "error": f"Failed to load plugin: {str(e)}"
            }
            
    def create_plugin(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """Create and register a new plugin.
        
        Args:
            name: Name of the plugin.
            description: Description of the plugin.
            capabilities: List of capabilities provided by the plugin.
            additional_context: Any additional context or requirements.
            
        Returns:
            Dictionary with the result of the plugin creation.
        """
        # Generate the plugin code
        result = self.generate_plugin(
            name=name,
            description=description,
            capabilities=capabilities,
            additional_context=additional_context
        )
        
        if "error" in result:
            return {"error": result["error"]}
            
        # Save the plugin
        save_result = self.save_plugin(name, result["plugin_code"])
        if "error" in save_result:
            return {"error": save_result["error"]}
            
        # Load and register the plugin
        plugin_file = save_result["file"]
        load_result = self.load_plugin(plugin_file)
        if "error" in load_result:
            return {"error": load_result["error"]}
            
        return {
            "success": True,
            "plugin_file": plugin_file
        }
