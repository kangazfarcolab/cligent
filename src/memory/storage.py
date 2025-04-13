"""
Memory storage for the CLI agent.
This module provides storage functionality for the agent's memory.
"""

import json
import time
from typing import Dict, List, Any, Optional, Union, Set


class MemoryStorage:
    """Storage for the agent's memory."""

    # Memory categories
    CATEGORY_COMMAND = "command"
    CATEGORY_PREFERENCE = "preference"
    CATEGORY_TOPIC = "topic"
    CATEGORY_GENERAL = "general"

    # Priority levels
    PRIORITY_HIGH = 3
    PRIORITY_MEDIUM = 2
    PRIORITY_LOW = 1

    def __init__(self):
        """Initialize the memory storage."""
        self.preferences: Dict[str, Any] = {}
        self.command_history: List[Dict[str, Any]] = []
        self.topics: Dict[str, Any] = {}
        self.last_accessed: Dict[str, float] = {}

        # New categorized memory storage
        self.categorized_memories: Dict[str, List[Dict[str, Any]]] = {
            self.CATEGORY_COMMAND: [],
            self.CATEGORY_PREFERENCE: [],
            self.CATEGORY_TOPIC: [],
            self.CATEGORY_GENERAL: []
        }

        # Tag index for quick lookup
        self.tag_index: Dict[str, List[Dict[str, Any]]] = {}

    def add_memory(self, content: str, category: str, tags: List[str] = None,
                  priority: int = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a memory item with categorization and tagging.

        Args:
            content: The memory content.
            category: The memory category.
            tags: Optional list of tags for the memory.
            priority: Priority level for the memory (higher is more important).
            metadata: Additional metadata for the memory.

        Returns:
            The created memory item.
        """
        # Set default values
        if tags is None:
            tags = []
        if priority is None:
            priority = self.PRIORITY_MEDIUM
        if metadata is None:
            metadata = {}

        # Ensure valid category
        if category not in self.categorized_memories:
            category = self.CATEGORY_GENERAL

        # Create memory item
        memory_item = {
            "content": content,
            "category": category,
            "tags": tags,
            "priority": priority,
            "metadata": metadata,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "access_count": 0
        }

        # Add to categorized memories
        self.categorized_memories[category].append(memory_item)

        # Add to tag index
        for tag in tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(memory_item)

        return memory_item

    def get_memories_by_category(self, category: str, limit: int = 10,
                               min_priority: int = None) -> List[Dict[str, Any]]:
        """Get memories by category.

        Args:
            category: The category to retrieve memories from.
            limit: Maximum number of memories to return.
            min_priority: Minimum priority level for memories.

        Returns:
            List of memory items.
        """
        if category not in self.categorized_memories:
            return []

        # Filter by priority if specified
        memories = self.categorized_memories[category]
        if min_priority is not None:
            memories = [m for m in memories if m["priority"] >= min_priority]

        # Sort by priority (high to low) and recency (newest first)
        sorted_memories = sorted(
            memories,
            key=lambda m: (m["priority"], m["last_accessed"]),
            reverse=True
        )

        # Update access metadata for returned memories
        for memory in sorted_memories[:limit]:
            memory["last_accessed"] = time.time()
            memory["access_count"] += 1

        return sorted_memories[:limit]

    def get_memories_by_tags(self, tags: List[str], require_all: bool = False,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Get memories by tags.

        Args:
            tags: List of tags to search for.
            require_all: If True, memories must have all tags. If False, any tag matches.
            limit: Maximum number of memories to return.

        Returns:
            List of memory items.
        """
        if not tags:
            return []

        # Get memories for each tag
        tag_memories: Dict[str, List[Dict[str, Any]]] = {}
        for tag in tags:
            tag_memories[tag] = self.tag_index.get(tag, [])

        # Combine memories based on require_all flag
        if require_all:
            # Find memories that have all tags
            result = []
            if tag_memories:
                # Start with memories from the first tag
                first_tag = tags[0]
                candidate_memories = set(tag_memories[first_tag])

                # Intersect with memories from other tags
                for tag in tags[1:]:
                    candidate_memories &= set(tag_memories[tag])

                result = list(candidate_memories)
        else:
            # Find memories that have any of the tags
            result = []
            for tag_memory_list in tag_memories.values():
                for memory in tag_memory_list:
                    if memory not in result:
                        result.append(memory)

        # Sort by priority and recency
        sorted_result = sorted(
            result,
            key=lambda m: (m["priority"], m["last_accessed"]),
            reverse=True
        )

        # Update access metadata
        for memory in sorted_result[:limit]:
            memory["last_accessed"] = time.time()
            memory["access_count"] += 1

        return sorted_result[:limit]

    def search_memories(self, query: str, categories: List[str] = None,
                      tags: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by content.

        Args:
            query: The search query.
            categories: Optional list of categories to search in.
            tags: Optional list of tags to filter by.
            limit: Maximum number of memories to return.

        Returns:
            List of matching memory items.
        """
        # Determine which categories to search
        search_categories = categories or list(self.categorized_memories.keys())

        # Get all memories from the specified categories
        all_memories = []
        for category in search_categories:
            if category in self.categorized_memories:
                all_memories.extend(self.categorized_memories[category])

        # Filter by tags if specified
        if tags:
            tag_memories = self.get_memories_by_tags(tags, require_all=False)
            all_memories = [m for m in all_memories if m in tag_memories]

        # Simple search by checking if query is in content
        # In a real implementation, this could use more sophisticated search
        query = query.lower()
        matching_memories = [
            m for m in all_memories
            if query in m["content"].lower()
        ]

        # Sort by relevance (priority and recency)
        sorted_matches = sorted(
            matching_memories,
            key=lambda m: (m["priority"], m["last_accessed"]),
            reverse=True
        )

        # Update access metadata
        for memory in sorted_matches[:limit]:
            memory["last_accessed"] = time.time()
            memory["access_count"] += 1

        return sorted_matches[:limit]

    def add_preference(self, key: str, value: Any) -> None:
        """Add a user preference.

        Args:
            key: The preference key.
            value: The preference value.
        """
        self.preferences[key] = value
        self.last_accessed[f"preference:{key}"] = time.time()

        # Also add to categorized memories
        content = f"User prefers {key}: {value}"
        metadata = {"preference_key": key, "preference_value": value}
        self.add_memory(
            content=content,
            category=self.CATEGORY_PREFERENCE,
            tags=["preference", key],
            priority=self.PRIORITY_HIGH,
            metadata=metadata
        )

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
        # Add to command history
        command_data = {
            "command": command,
            "output": output,
            "success": success,
            "timestamp": time.time()
        }
        self.command_history.append(command_data)

        # Limit history size
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]

        # Add to categorized memories
        content = f"Command: {command}\nSuccess: {success}"
        metadata = {"command": command, "output": output, "success": success}

        # Determine tags based on command content
        tags = ["command"]
        if "file" in command or "ls" in command or "cd" in command:
            tags.append("file_operation")
        if "network" in command or "curl" in command or "wget" in command:
            tags.append("network_operation")
        if "process" in command or "kill" in command or "ps" in command:
            tags.append("process_management")

        # Determine priority based on success and complexity
        priority = self.PRIORITY_MEDIUM
        if not success:
            priority = self.PRIORITY_HIGH  # Failed commands are important to remember
        if len(command) > 50:
            priority = self.PRIORITY_HIGH  # Complex commands are important

        self.add_memory(
            content=content,
            category=self.CATEGORY_COMMAND,
            tags=tags,
            priority=priority,
            metadata=metadata
        )

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

        # Add to categorized memories
        content = f"Topic: {topic}\nDetails: {details}"
        metadata = {"topic": topic, "details": details}
        self.add_memory(
            content=content,
            category=self.CATEGORY_TOPIC,
            tags=["topic", topic],
            priority=self.PRIORITY_MEDIUM,
            metadata=metadata
        )

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

    def get_most_relevant_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most relevant memories based on priority, recency, and access count.

        Args:
            limit: Maximum number of memories to return.

        Returns:
            List of relevant memory items.
        """
        # Collect all memories
        all_memories = []
        for category_memories in self.categorized_memories.values():
            all_memories.extend(category_memories)

        # Calculate relevance score for each memory
        # Formula: priority * 10 + recency_factor * 5 + access_count
        current_time = time.time()
        for memory in all_memories:
            recency_factor = 1.0 / (1.0 + (current_time - memory["last_accessed"]) / 86400)  # Days factor
            memory["relevance_score"] = (
                memory["priority"] * 10 +
                recency_factor * 5 +
                memory["access_count"]
            )

        # Sort by relevance score
        sorted_memories = sorted(
            all_memories,
            key=lambda m: m["relevance_score"],
            reverse=True
        )

        # Update access metadata
        for memory in sorted_memories[:limit]:
            memory["last_accessed"] = time.time()
            memory["access_count"] += 1

        return sorted_memories[:limit]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory to a dictionary.

        Returns:
            The memory as a dictionary.
        """
        return {
            "preferences": self.preferences,
            "command_history": self.command_history,
            "topics": self.topics,
            "last_accessed": self.last_accessed,
            "categorized_memories": self.categorized_memories,
            "tag_index": self.tag_index
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
        memory.categorized_memories = data.get("categorized_memories", {
            cls.CATEGORY_COMMAND: [],
            cls.CATEGORY_PREFERENCE: [],
            cls.CATEGORY_TOPIC: [],
            cls.CATEGORY_GENERAL: []
        })

        # Rebuild tag index
        memory.tag_index = {}
        for category, memories in memory.categorized_memories.items():
            for mem in memories:
                for tag in mem.get("tags", []):
                    if tag not in memory.tag_index:
                        memory.tag_index[tag] = []
                    memory.tag_index[tag].append(mem)

        return memory
