"""
Feedback system for the CLI agent.
This module provides functionality for tracking and analyzing user feedback.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

from .storage import MemoryStorage


class FeedbackTracker:
    """Tracker for user feedback on agent responses and suggestions."""
    
    # Feedback types
    FEEDBACK_POSITIVE = "positive"
    FEEDBACK_NEGATIVE = "negative"
    FEEDBACK_NEUTRAL = "neutral"
    
    # Feedback categories
    CATEGORY_RESPONSE = "response"
    CATEGORY_SUGGESTION = "suggestion"
    CATEGORY_COMMAND = "command"
    
    def __init__(self, storage: Optional[MemoryStorage] = None):
        """Initialize the feedback tracker.
        
        Args:
            storage: The memory storage to use. If None, a new one is created.
        """
        self.storage = storage or MemoryStorage()
        self.logger = logging.getLogger(__name__)
        self.feedback_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics: Dict[str, Dict[str, Any]] = {
            self.CATEGORY_RESPONSE: {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            self.CATEGORY_SUGGESTION: {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            self.CATEGORY_COMMAND: {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
        }
    
    def add_feedback(self, feedback_type: str, category: str, content: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add feedback to the tracker.
        
        Args:
            feedback_type: The type of feedback (positive, negative, neutral).
            category: The category of the feedback (response, suggestion, command).
            content: The content that received feedback.
            metadata: Additional metadata about the feedback.
            
        Returns:
            The created feedback entry.
        """
        # Validate feedback type
        if feedback_type not in [self.FEEDBACK_POSITIVE, self.FEEDBACK_NEGATIVE, self.FEEDBACK_NEUTRAL]:
            feedback_type = self.FEEDBACK_NEUTRAL
        
        # Validate category
        if category not in [self.CATEGORY_RESPONSE, self.CATEGORY_SUGGESTION, self.CATEGORY_COMMAND]:
            category = self.CATEGORY_RESPONSE
        
        # Create feedback entry
        feedback_entry = {
            "feedback_type": feedback_type,
            "category": category,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        
        # Add to history
        self.feedback_history.append(feedback_entry)
        
        # Update metrics
        self.metrics[category]["total"] += 1
        self.metrics[category][feedback_type] += 1
        
        # Add to memory storage
        self._add_to_memory(feedback_entry)
        
        return feedback_entry
    
    def _add_to_memory(self, feedback_entry: Dict[str, Any]) -> None:
        """Add feedback to memory storage.
        
        Args:
            feedback_entry: The feedback entry to add.
        """
        feedback_type = feedback_entry["feedback_type"]
        category = feedback_entry["category"]
        content = feedback_entry["content"]
        
        # Create memory content
        memory_content = f"User gave {feedback_type} feedback on {category}: {content}"
        
        # Determine tags
        tags = ["feedback", feedback_type, category]
        
        # Determine priority
        priority = self.storage.PRIORITY_MEDIUM
        if feedback_type == self.FEEDBACK_NEGATIVE:
            priority = self.storage.PRIORITY_HIGH  # Negative feedback is important
        
        # Add to memory
        self.storage.add_memory(
            content=memory_content,
            category=self.storage.CATEGORY_GENERAL,
            tags=tags,
            priority=priority,
            metadata=feedback_entry
        )
    
    def get_feedback_stats(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get feedback statistics.
        
        Args:
            category: Optional category to filter by.
            
        Returns:
            Dictionary of feedback statistics.
        """
        if category and category in self.metrics:
            stats = self.metrics[category].copy()
            
            # Calculate percentages
            total = stats["total"]
            if total > 0:
                stats["positive_percent"] = (stats["positive"] / total) * 100
                stats["negative_percent"] = (stats["negative"] / total) * 100
                stats["neutral_percent"] = (stats["neutral"] / total) * 100
            else:
                stats["positive_percent"] = 0
                stats["negative_percent"] = 0
                stats["neutral_percent"] = 0
            
            return stats
        else:
            # Combine all categories
            combined = {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }
            
            for cat_metrics in self.metrics.values():
                combined["total"] += cat_metrics["total"]
                combined["positive"] += cat_metrics["positive"]
                combined["negative"] += cat_metrics["negative"]
                combined["neutral"] += cat_metrics["neutral"]
            
            # Calculate percentages
            total = combined["total"]
            if total > 0:
                combined["positive_percent"] = (combined["positive"] / total) * 100
                combined["negative_percent"] = (combined["negative"] / total) * 100
                combined["neutral_percent"] = (combined["neutral"] / total) * 100
            else:
                combined["positive_percent"] = 0
                combined["negative_percent"] = 0
                combined["neutral_percent"] = 0
            
            return combined
    
    def get_recent_feedback(self, count: int = 5, 
                          feedback_type: Optional[str] = None,
                          category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent feedback entries.
        
        Args:
            count: Number of entries to return.
            feedback_type: Optional feedback type to filter by.
            category: Optional category to filter by.
            
        Returns:
            List of recent feedback entries.
        """
        # Filter feedback history
        filtered = self.feedback_history
        
        if feedback_type:
            filtered = [f for f in filtered if f["feedback_type"] == feedback_type]
        
        if category:
            filtered = [f for f in filtered if f["category"] == category]
        
        # Sort by timestamp (newest first)
        sorted_feedback = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)
        
        return sorted_feedback[:count]
    
    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """Analyze feedback trends over time.
        
        Returns:
            Dictionary of trend analysis.
        """
        # Simple trend analysis
        trends = {}
        
        # Get feedback from last 24 hours
        recent_cutoff = time.time() - (24 * 60 * 60)
        recent_feedback = [f for f in self.feedback_history if f["timestamp"] > recent_cutoff]
        
        # Calculate recent metrics
        recent_metrics = {
            self.CATEGORY_RESPONSE: {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            self.CATEGORY_SUGGESTION: {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            self.CATEGORY_COMMAND: {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
        }
        
        for feedback in recent_feedback:
            category = feedback["category"]
            feedback_type = feedback["feedback_type"]
            recent_metrics[category]["total"] += 1
            recent_metrics[category][feedback_type] += 1
        
        # Compare with overall metrics to identify trends
        for category, metrics in self.metrics.items():
            if metrics["total"] == 0:
                continue
                
            recent = recent_metrics[category]
            if recent["total"] == 0:
                continue
            
            # Calculate percentages
            overall_positive_pct = (metrics["positive"] / metrics["total"]) * 100
            recent_positive_pct = (recent["positive"] / recent["total"]) * 100
            
            # Determine trend
            trend = "stable"
            if recent_positive_pct > overall_positive_pct + 10:
                trend = "improving"
            elif recent_positive_pct < overall_positive_pct - 10:
                trend = "declining"
            
            trends[category] = {
                "trend": trend,
                "recent_positive_pct": recent_positive_pct,
                "overall_positive_pct": overall_positive_pct,
                "change": recent_positive_pct - overall_positive_pct
            }
        
        return trends
    
    def get_feedback_context(self) -> str:
        """Get feedback context for the LLM.
        
        Returns:
            A string containing relevant feedback context.
        """
        context_parts = []
        
        # Add overall stats
        stats = self.get_feedback_stats()
        if stats["total"] > 0:
            stats_str = f"Overall feedback: {stats['positive']} positive, {stats['negative']} negative, {stats['neutral']} neutral"
            context_parts.append(stats_str)
        
        # Add recent feedback
        recent = self.get_recent_feedback(3)
        if recent:
            recent_parts = ["Recent feedback:"]
            for feedback in recent:
                feedback_type = feedback["feedback_type"]
                category = feedback["category"]
                content = feedback["content"]
                recent_parts.append(f"- {feedback_type.capitalize()} feedback on {category}: {content}")
            
            context_parts.append("\n".join(recent_parts))
        
        # Add trends
        trends = self.analyze_feedback_trends()
        if trends:
            trend_parts = ["Feedback trends:"]
            for category, trend_data in trends.items():
                trend = trend_data["trend"]
                trend_parts.append(f"- {category.capitalize()}: {trend} ({trend_data['recent_positive_pct']:.1f}% positive recently)")
            
            context_parts.append("\n".join(trend_parts))
        
        return "\n\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the feedback tracker to a dictionary.
        
        Returns:
            The feedback tracker as a dictionary.
        """
        return {
            "feedback_history": self.feedback_history,
            "metrics": self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], storage: Optional[MemoryStorage] = None) -> 'FeedbackTracker':
        """Create a feedback tracker from a dictionary.
        
        Args:
            data: The dictionary to create the feedback tracker from.
            storage: Optional memory storage to use.
            
        Returns:
            The created feedback tracker.
        """
        tracker = cls(storage)
        tracker.feedback_history = data.get("feedback_history", [])
        tracker.metrics = data.get("metrics", {
            cls.CATEGORY_RESPONSE: {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            cls.CATEGORY_SUGGESTION: {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            cls.CATEGORY_COMMAND: {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
        })
        
        return tracker
