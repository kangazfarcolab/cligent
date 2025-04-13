"""
Memory storage for the CLI agent.
This module provides storage functionality for the agent's memory.
"""

import json
import time
from typing import Dict, List, Any, Optional, Union


class MemoryStorage:
    """Storage for the agent's memory."""
    
    def __init__(self):
        """Initialize the memory storage."""
        self.preferences: Dict[str, Any] = {}
        self.command_history: List[Dict[str, Any]] = []
        self.topics: Dict[str, Any] = {}
        self.last_accessed: Dict[str, float] = {}
    
    def add_preference(self, key: str, value: Any) -> None:
        """Add a user preference.
        
        Args:
            key: The preference key.
            value: The preference value.
        """
        self.preferences[key] = value
        self.last_accessed[f"preference:{key}"] = time.time()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference.
        
        Args:
            key: The preference key.
            default: The default value if the preference doesn't exist.
            
        Returns:
            The preference value, or the default if it doesn't exist.
        """
        self.last_accessed[f"preference:{key}"] = time.time()
        return self.preferences.get(key, default)
    
    def add_command(self, command: str, output: str, success: bool) -> None:
        """Add a command to the history.
        
        Args:
            command: The command that was executed.
            output: The command output.
            success: Whether the command was successful.
        """
        self.command_history.append({
            "command": command,
            "output": output,
            "success": success,
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]
    
    def get_recent_commands(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent commands.
        
        Args:
            count: The number of commands to return.
            
        Returns:
            The most recent commands.
        """
        return self.command_history[-count:]
    
    def add_topic(self, topic: str, details: Any) -> None:
        """Add a topic to the memory.
        
        Args:
            topic: The topic name.
            details: The topic details.
        """
        self.topics[topic] = details
        self.last_accessed[f"topic:{topic}"] = time.time()
    
    def get_topic(self, topic: str, default: Any = None) -> Any:
        """Get a topic from the memory.
        
        Args:
            topic: The topic name.
            default: The default value if the topic doesn't exist.
            
        Returns:
            The topic details, or the default if it doesn't exist.
        """
        self.last_accessed[f"topic:{topic}"] = time.time()
        return self.topics.get(topic, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory to a dictionary.
        
        Returns:
            The memory as a dictionary.
        """
        return {
            "preferences": self.preferences,
            "command_history": self.command_history,
            "topics": self.topics,
            "last_accessed": self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryStorage':
        """Create a memory storage from a dictionary.
        
        Args:
            data: The dictionary to create the memory from.
            
        Returns:
            The created memory storage.
        """
        memory = cls()
        memory.preferences = data.get("preferences", {})
        memory.command_history = data.get("command_history", [])
        memory.topics = data.get("topics", {})
        memory.last_accessed = data.get("last_accessed", {})
        return memory
