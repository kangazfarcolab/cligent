"""
Memory manager for the CLI agent.
This module provides memory management functionality.
"""

import time
import logging
import re
from typing import Dict, List, Any, Optional, Union, Set, Tuple

from .storage import MemoryStorage


class MemoryManager:
    """Manager for the agent's memory."""

    # Maximum number of memories to include in context
    MAX_CONTEXT_MEMORIES = 10

    # Memory summarization thresholds
    SUMMARIZATION_AGE_THRESHOLD = 7 * 86400  # 7 days in seconds
    SUMMARIZATION_COUNT_THRESHOLD = 50  # Summarize when more than 50 memories in a category

    def __init__(self, storage: Optional[MemoryStorage] = None):
        """Initialize the memory manager.

        Args:
            storage: The memory storage to use. If None, a new one is created.
        """
        self.storage = storage or MemoryStorage()
        self.logger = logging.getLogger(__name__)
        self.summarized_memories: Dict[str, Dict[str, Any]] = {}

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

        # Check if summarization is needed
        self._check_and_summarize_memories()

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

        # Add most relevant memories
        relevant_memories = self.storage.get_most_relevant_memories(self.MAX_CONTEXT_MEMORIES)
        if relevant_memories:
            memories = []
            for memory in relevant_memories:
                # Format based on category
                if memory["category"] == self.storage.CATEGORY_PREFERENCE:
                    memories.append(f"- Preference: {memory['content']}")
                elif memory["category"] == self.storage.CATEGORY_COMMAND:
                    memories.append(f"- Command: {memory['content']}")
                elif memory["category"] == self.storage.CATEGORY_TOPIC:
                    memories.append(f"- Topic: {memory['content']}")
                else:
                    memories.append(f"- {memory['content']}")

            if memories:
                context_parts.append("Relevant memories:\n" + "\n".join(memories))

        # Add memory summaries if available
        if self.summarized_memories:
            summaries = []
            for category, summary in self.summarized_memories.items():
                summaries.append(f"- {category.capitalize()}: {summary['content']}")

            if summaries:
                context_parts.append("Memory summaries:\n" + "\n".join(summaries))

        return "\n\n".join(context_parts)

    def _check_and_summarize_memories(self) -> None:
        """Check if memory summarization is needed and perform it if necessary."""
        current_time = time.time()

        # Check each category for summarization
        for category, memories in self.storage.categorized_memories.items():
            # Skip if not enough memories
            if len(memories) < self.SUMMARIZATION_COUNT_THRESHOLD:
                continue

            # Find old memories that need summarization
            old_memories = [
                m for m in memories
                if (current_time - m["created_at"]) > self.SUMMARIZATION_AGE_THRESHOLD
            ]

            # Skip if not enough old memories
            if len(old_memories) < 10:  # Need at least 10 old memories to summarize
                continue

            # Summarize memories
            self._summarize_memories(category, old_memories)

    def _summarize_memories(self, category: str, memories: List[Dict[str, Any]]) -> None:
        """Summarize a list of memories.

        Args:
            category: The category of memories to summarize.
            memories: The memories to summarize.
        """
        # Group memories by tags
        tag_groups: Dict[str, List[Dict[str, Any]]] = {}
        for memory in memories:
            for tag in memory.get("tags", []):
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(memory)

        # Create summaries for each tag group
        for tag, tag_memories in tag_groups.items():
            if len(tag_memories) < 5:  # Skip small groups
                continue

            # Create a simple summary by extracting key information
            if category == self.storage.CATEGORY_COMMAND:
                summary = self._summarize_command_memories(tag_memories)
            elif category == self.storage.CATEGORY_PREFERENCE:
                summary = self._summarize_preference_memories(tag_memories)
            elif category == self.storage.CATEGORY_TOPIC:
                summary = self._summarize_topic_memories(tag_memories)
            else:
                summary = self._summarize_general_memories(tag_memories)

            # Store the summary
            summary_key = f"{category}:{tag}"
            self.summarized_memories[summary_key] = {
                "category": category,
                "tag": tag,
                "content": summary,
                "count": len(tag_memories),
                "created_at": time.time()
            }

    def _summarize_command_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize command memories.

        Args:
            memories: The command memories to summarize.

        Returns:
            A summary of the command memories.
        """
        # Count command successes and failures
        total = len(memories)
        successful = sum(1 for m in memories if m.get("metadata", {}).get("success", False))
        failed = total - successful

        # Extract common command patterns
        commands = [m.get("metadata", {}).get("command", "") for m in memories]
        common_commands = self._extract_common_patterns(commands)

        # Create summary
        summary = f"User has executed {total} commands related to this topic. "
        summary += f"{successful} were successful, {failed} failed. "

        if common_commands:
            summary += "Common command patterns: " + ", ".join(common_commands[:3])

        return summary

    def _summarize_preference_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize preference memories.

        Args:
            memories: The preference memories to summarize.

        Returns:
            A summary of the preference memories.
        """
        # Extract preference keys and values
        preferences: Dict[str, List[Any]] = {}
        for memory in memories:
            key = memory.get("metadata", {}).get("preference_key")
            value = memory.get("metadata", {}).get("preference_value")
            if key:
                if key not in preferences:
                    preferences[key] = []
                preferences[key].append(value)

        # Create summary
        summary_parts = []
        for key, values in preferences.items():
            # Get the most recent value
            current_value = values[-1] if values else None
            summary_parts.append(f"{key}: {current_value}")

        return "User preferences: " + ", ".join(summary_parts)

    def _summarize_topic_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize topic memories.

        Args:
            memories: The topic memories to summarize.

        Returns:
            A summary of the topic memories.
        """
        # Extract topics
        topics = [m.get("metadata", {}).get("topic", "") for m in memories]
        topic_counts: Dict[str, int] = {}
        for topic in topics:
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Sort topics by frequency
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

        # Create summary
        if sorted_topics:
            top_topics = [t[0] for t in sorted_topics[:3]]
            summary = f"User has shown interest in these topics: {', '.join(top_topics)}"
        else:
            summary = "User has shown interest in various topics."

        return summary

    def _summarize_general_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize general memories.

        Args:
            memories: The general memories to summarize.

        Returns:
            A summary of the general memories.
        """
        # Extract content
        contents = [m.get("content", "") for m in memories]

        # Create a simple summary
        return f"User has {len(memories)} memories related to this topic."

    def _extract_common_patterns(self, strings: List[str]) -> List[str]:
        """Extract common patterns from a list of strings.

        Args:
            strings: The strings to extract patterns from.

        Returns:
            A list of common patterns.
        """
        # Simple implementation: just return the most common strings
        # In a real implementation, this could use more sophisticated pattern extraction
        string_counts: Dict[str, int] = {}
        for s in strings:
            string_counts[s] = string_counts.get(s, 0) + 1

        # Sort by frequency
        sorted_strings = sorted(string_counts.items(), key=lambda x: x[1], reverse=True)

        # Return the most common strings
        return [s[0] for s in sorted_strings[:5]]

    def update_from_user_input(self, user_input: str) -> None:
        """Update the memory based on user input.

        Args:
            user_input: The user input to process.
        """
        # Extract topics from user input
        self._extract_topics_from_input(user_input)

        # Extract preferences from user input
        self._extract_preferences_from_input(user_input)

        # Add general memory about user input
        self._add_general_memory_from_input(user_input)

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

        # Check for programming languages
        programming_languages = [
            "python", "javascript", "java", "c++", "c#", "ruby", "go", "rust",
            "php", "typescript", "kotlin", "swift", "scala", "perl", "bash", "shell"
        ]
        for lang in programming_languages:
            if lang in lower_input:
                self.storage.add_topic(f"{lang}_programming", f"User has been working with {lang}")

    def _extract_preferences_from_input(self, user_input: str) -> None:
        """Extract preferences from user input.

        Args:
            user_input: The user input to extract preferences from.
        """
        lower_input = user_input.lower()

        # Check for explicit preference statements
        preference_patterns = [
            (r"i prefer (\w+)", "preferred_tool"),
            (r"i like (\w+)", "liked_tool"),
            (r"i want (\w+)", "wanted_feature"),
            (r"i need (\w+)", "needed_feature"),
            (r"i use (\w+)", "used_tool")
        ]

        for pattern, pref_key in preference_patterns:
            matches = re.findall(pattern, lower_input)
            for match in matches:
                self.storage.add_preference(pref_key, match)

    def _add_general_memory_from_input(self, user_input: str) -> None:
        """Add general memory from user input.

        Args:
            user_input: The user input to add memory from.
        """
        # Skip very short inputs
        if len(user_input) < 10:
            return

        # Add as general memory with appropriate tags
        tags = ["user_input"]

        # Add sentiment tags
        positive_words = ["thanks", "good", "great", "excellent", "awesome", "like", "love"]
        negative_words = ["bad", "terrible", "hate", "dislike", "wrong", "error", "issue", "problem"]

        lower_input = user_input.lower()
        if any(word in lower_input for word in positive_words):
            tags.append("positive_sentiment")
        if any(word in lower_input for word in negative_words):
            tags.append("negative_sentiment")

        # Add question tag
        if "?" in user_input or lower_input.startswith("how") or lower_input.startswith("what") or lower_input.startswith("why"):
            tags.append("question")

        # Add memory
        self.storage.add_memory(
            content=f"User said: {user_input}",
            category=self.storage.CATEGORY_GENERAL,
            tags=tags,
            priority=self.storage.PRIORITY_MEDIUM,
            metadata={"input": user_input, "timestamp": time.time()}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory manager to a dictionary.

        Returns:
            The memory manager as a dictionary.
        """
        return {
            "storage": self.storage.to_dict(),
            "summarized_memories": self.summarized_memories
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryManager':
        """Create a memory manager from a dictionary.

        Args:
            data: The dictionary to create the memory manager from.

        Returns:
            The created memory manager.
        """
        if isinstance(data, dict) and "storage" in data:
            storage = MemoryStorage.from_dict(data["storage"])
            manager = cls(storage)
            manager.summarized_memories = data.get("summarized_memories", {})
            return manager
        else:
            # Handle legacy format where data is just the storage
            storage = MemoryStorage.from_dict(data)
            return cls(storage)
