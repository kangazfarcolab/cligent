"""
CLI feedback commands for the agent.
This module provides CLI commands for user feedback.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from ..memory.feedback import FeedbackTracker


logger = logging.getLogger(__name__)


class FeedbackCommands:
    """CLI commands for providing feedback to the agent."""
    
    def __init__(self, feedback_tracker: FeedbackTracker):
        """Initialize the feedback commands.
        
        Args:
            feedback_tracker: The feedback tracker to use.
        """
        self.feedback_tracker = feedback_tracker
    
    def process_feedback_command(self, command: str) -> Tuple[bool, str]:
        """Process a feedback command.
        
        Args:
            command: The command to process.
            
        Returns:
            A tuple of (success, message).
        """
        # Check if this is a feedback command
        if not self._is_feedback_command(command):
            return False, "Not a feedback command"
        
        # Parse the command
        parts = command.strip().split(" ", 2)
        
        # Handle different feedback commands
        if parts[0] == "feedback":
            if len(parts) < 2:
                return False, "Invalid feedback command. Usage: feedback [positive|negative|neutral] [content]"
            
            feedback_type = parts[1].lower()
            content = parts[2] if len(parts) > 2 else ""
            
            return self._handle_feedback(feedback_type, content)
        
        elif parts[0] == "helpful":
            content = parts[1] if len(parts) > 1 else "The last response was helpful"
            return self._handle_feedback("positive", content)
        
        elif parts[0] == "unhelpful":
            content = parts[1] if len(parts) > 1 else "The last response was not helpful"
            return self._handle_feedback("negative", content)
        
        elif parts[0] == "stats":
            return self._handle_stats()
        
        return False, "Unknown feedback command"
    
    def _is_feedback_command(self, command: str) -> bool:
        """Check if a command is a feedback command.
        
        Args:
            command: The command to check.
            
        Returns:
            True if the command is a feedback command, False otherwise.
        """
        command = command.strip().lower()
        return (
            command.startswith("feedback ") or
            command.startswith("helpful") or
            command.startswith("unhelpful") or
            command == "stats"
        )
    
    def _handle_feedback(self, feedback_type: str, content: str) -> Tuple[bool, str]:
        """Handle a feedback command.
        
        Args:
            feedback_type: The type of feedback.
            content: The feedback content.
            
        Returns:
            A tuple of (success, message).
        """
        # Map feedback type to internal constants
        if feedback_type in ["positive", "good", "helpful", "yes", "y"]:
            internal_type = self.feedback_tracker.FEEDBACK_POSITIVE
        elif feedback_type in ["negative", "bad", "unhelpful", "no", "n"]:
            internal_type = self.feedback_tracker.FEEDBACK_NEGATIVE
        else:
            internal_type = self.feedback_tracker.FEEDBACK_NEUTRAL
        
        # Add the feedback
        self.feedback_tracker.add_feedback(
            feedback_type=internal_type,
            category=self.feedback_tracker.CATEGORY_RESPONSE,
            content=content
        )
        
        # Return success message
        return True, f"Thank you for your {internal_type} feedback!"
    
    def _handle_stats(self) -> Tuple[bool, str]:
        """Handle a stats command.
        
        Returns:
            A tuple of (success, message).
        """
        # Get feedback stats
        stats = self.feedback_tracker.get_feedback_stats()
        
        # Format stats message
        if stats["total"] == 0:
            message = "No feedback has been provided yet."
        else:
            message = f"Feedback stats:\n"
            message += f"Total: {stats['total']}\n"
            message += f"Positive: {stats['positive']} ({stats['positive_percent']:.1f}%)\n"
            message += f"Negative: {stats['negative']} ({stats['negative_percent']:.1f}%)\n"
            message += f"Neutral: {stats['neutral']} ({stats['neutral_percent']:.1f}%)"
        
        return True, message
    
    def get_help_text(self) -> str:
        """Get help text for feedback commands.
        
        Returns:
            Help text for feedback commands.
        """
        return """
Feedback Commands:
  feedback positive [content]  - Provide positive feedback
  feedback negative [content]  - Provide negative feedback
  helpful [content]            - Shorthand for positive feedback
  unhelpful [content]          - Shorthand for negative feedback
  stats                        - Show feedback statistics
"""
