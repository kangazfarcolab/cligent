"""
Memory manager for the CLI agent.
This module provides memory management functionality.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union

from .storage import MemoryStorage


class MemoryManager:
    """Manager for the agent's memory."""
    
    def __init__(self, storage: Optional[MemoryStorage] = None):
        """Initialize the memory manager.
        
        Args:
            storage: The memory storage to use. If None, a new one is created.
        """
        self.storage = storage or MemoryStorage()
        self.logger = logging.getLogger(__name__)
    
    def add_command_to_memory(self, command: str, output: str, success: bool) -> None:
        """Add a command to the memory.
        
        Args:
            command: The command that was executed.
            output: The command output.
            success: Whether the command was successful.
        """
        self.storage.add_command(command, output, success)
        
        # Try to extract preferences from commands
        self._extract_preferences_from_command(command)
    
    def _extract_preferences_from_command(self, command: str) -> None:
        """Extract preferences from a command.
        
        Args:
            command: The command to extract preferences from.
        """
        # Extract editor preference
        if command.startswith("vim ") or command.startswith("vi "):
            self.storage.add_preference("preferred_editor", "vim")
        elif command.startswith("nano "):
            self.storage.add_preference("preferred_editor", "nano")
        elif command.startswith("emacs "):
            self.storage.add_preference("preferred_editor", "emacs")
        
        # Extract shell preference
        if "bash" in command:
            self.storage.add_preference("preferred_shell", "bash")
        elif "zsh" in command:
            self.storage.add_preference("preferred_shell", "zsh")
        elif "fish" in command:
            self.storage.add_preference("preferred_shell", "fish")
        
        # Extract verbosity preference
        if "-v" in command or "--verbose" in command:
            self.storage.add_preference("verbose_output", True)
    
    def get_memory_context(self) -> str:
        """Get context from the memory for the LLM.
        
        Returns:
            A string containing relevant memory context.
        """
        context_parts = []
        
        # Add preferences
        if self.storage.preferences:
            prefs = []
            for key, value in self.storage.preferences.items():
                prefs.append(f"{key}: {value}")
            
            if prefs:
                context_parts.append("User preferences:\n" + "\n".join(prefs))
        
        # Add recent commands
        recent_commands = self.storage.get_recent_commands(5)
        if recent_commands:
            cmds = []
            for cmd in recent_commands:
                success_str = "successful" if cmd.get("success", False) else "failed"
                cmds.append(f"- {cmd['command']} ({success_str})")
            
            if cmds:
                context_parts.append("Recent commands:\n" + "\n".join(cmds))
        
        # Add relevant topics
        relevant_topics = self._get_relevant_topics()
        if relevant_topics:
            topics = []
            for topic, details in relevant_topics.items():
                topics.append(f"- {topic}: {details}")
            
            if topics:
                context_parts.append("Relevant topics:\n" + "\n".join(topics))
        
        return "\n\n".join(context_parts)
    
    def _get_relevant_topics(self) -> Dict[str, Any]:
        """Get relevant topics from the memory.
        
        Returns:
            A dictionary of relevant topics.
        """
        # For now, just return all topics
        # In a more sophisticated implementation, we could filter by relevance
        return self.storage.topics
    
    def update_from_user_input(self, user_input: str) -> None:
        """Update the memory based on user input.
        
        Args:
            user_input: The user input to process.
        """
        # Extract topics from user input
        self._extract_topics_from_input(user_input)
    
    def _extract_topics_from_input(self, user_input: str) -> None:
        """Extract topics from user input.
        
        Args:
            user_input: The user input to extract topics from.
        """
        # Simple topic extraction based on keywords
        lower_input = user_input.lower()
        
        # Check for file operations
        if any(kw in lower_input for kw in ["file", "directory", "folder", "path"]):
            self.storage.add_topic("file_operations", "User has been working with files and directories")
        
        # Check for network operations
        if any(kw in lower_input for kw in ["network", "http", "curl", "wget", "download"]):
            self.storage.add_topic("network_operations", "User has been working with network operations")
        
        # Check for process management
        if any(kw in lower_input for kw in ["process", "kill", "background", "foreground", "job"]):
            self.storage.add_topic("process_management", "User has been working with process management")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory manager to a dictionary.
        
        Returns:
            The memory manager as a dictionary.
        """
        return self.storage.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryManager':
        """Create a memory manager from a dictionary.
        
        Args:
            data: The dictionary to create the memory manager from.
            
        Returns:
            The created memory manager.
        """
        storage = MemoryStorage.from_dict(data)
        return cls(storage)
