"""
State management for the CLI agent.
This module provides state management functionality for the CLI agent.
"""

import os
import json
import time
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict


class MessageRole(Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """Message in a conversation."""

    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a message from a dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class Conversation:
    """Conversation history."""

    messages: List[Message] = field(default_factory=list)

    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the conversation.

        Args:
            role: Role of the message sender.
            content: Content of the message.
        """
        self.messages.append(Message(role=role, content=content))

    def get_messages(self, max_messages: Optional[int] = None) -> List[Message]:
        """Get messages from the conversation.

        Args:
            max_messages: Maximum number of messages to return, starting from the most recent.
                If None, returns all messages.

        Returns:
            List of messages.
        """
        if max_messages is None:
            return self.messages
        return self.messages[-max_messages:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the conversation to a dictionary."""
        return {
            "messages": [message.to_dict() for message in self.messages],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create a conversation from a dictionary."""
        return cls(
            messages=[Message.from_dict(message) for message in data["messages"]],
        )


@dataclass
class AgentState:
    """State of the CLI agent."""

    conversation: Conversation = field(default_factory=Conversation)
    working_directory: str = field(default_factory=os.getcwd)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    feedback: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary."""
        return {
            "conversation": self.conversation.to_dict(),
            "working_directory": self.working_directory,
            "environment_vars": self.environment_vars,
            "command_history": self.command_history,
            "memory": self.memory,
            "feedback": self.feedback,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create a state from a dictionary."""
        return cls(
            conversation=Conversation.from_dict(data["conversation"]),
            working_directory=data["working_directory"],
            environment_vars=data["environment_vars"],
            command_history=data["command_history"],
            memory=data.get("memory", {}),
            feedback=data.get("feedback", {}),
        )

    def save(self, filepath: str) -> None:
        """Save the state to a file.

        Args:
            filepath: Path to the file.
        """
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "AgentState":
        """Load the state from a file.

        Args:
            filepath: Path to the file.

        Returns:
            Loaded state.
        """
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
