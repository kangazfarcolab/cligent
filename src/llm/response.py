"""
Response parsing utilities for the LLM.
This module provides utilities for parsing and processing responses from the LLM.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum, auto


class ResponseType(Enum):
    """Types of responses from the LLM."""
    COMMAND = auto()  # Response contains a command to execute
    ANALYSIS = auto()  # Response contains analysis of command output
    ERROR = auto()  # Response contains error handling
    GENERAL = auto()  # General response with no specific type


@dataclass
class ParsedCommand:
    """Parsed command from an LLM response."""
    command: str
    explanation: str
    is_safe: bool
    safety_reasoning: Optional[str] = None


@dataclass
class ParsedAnalysis:
    """Parsed analysis of command output."""
    summary: str
    errors_detected: bool
    warnings_detected: bool
    key_points: List[str]
    next_steps: List[str]


@dataclass
class ParsedResponse:
    """Parsed response from the LLM."""
    type: ResponseType
    content: str
    command: Optional[ParsedCommand] = None
    analysis: Optional[ParsedAnalysis] = None


def extract_code_blocks(text: str) -> List[str]:
    """Extract code blocks from markdown text.
    
    Args:
        text: The text containing markdown code blocks.
        
    Returns:
        List of extracted code blocks.
    """
    # Match code blocks with triple backticks
    pattern = r"```(?:\w+)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    # Also match inline code blocks with single backticks
    if not matches:
        pattern = r"`(.*?)`"
        matches = re.findall(pattern, text)
    
    return [match.strip() for match in matches]


def extract_command(text: str) -> Optional[str]:
    """Extract a command from the LLM response.
    
    Args:
        text: The LLM response text.
        
    Returns:
        The extracted command, or None if no command is found.
    """
    code_blocks = extract_code_blocks(text)
    if code_blocks:
        return code_blocks[0]
    
    # If no code blocks, look for lines that look like commands
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("$") or line.startswith(">"):
            return line[1:].strip()
    
    return None


def parse_safety_assessment(text: str) -> Tuple[bool, Optional[str]]:
    """Parse the safety assessment from the LLM response.
    
    Args:
        text: The LLM response text.
        
    Returns:
        Tuple of (is_safe, reasoning)
    """
    # Look for explicit statements about safety
    is_safe = True
    reasoning = None
    
    lower_text = text.lower()
    
    # Check for unsafe indicators
    unsafe_phrases = [
        "not safe", "unsafe", "dangerous", "harmful", 
        "should not run", "don't run", "do not run",
        "could damage", "might damage", "would damage",
        "security risk", "security concern"
    ]
    
    for phrase in unsafe_phrases:
        if phrase in lower_text:
            is_safe = False
            # Try to extract the reasoning
            sentence_pattern = r"[^.!?]*" + re.escape(phrase) + r"[^.!?]*[.!?]"
            matches = re.findall(sentence_pattern, lower_text)
            if matches:
                reasoning = matches[0].strip()
            break
    
    return is_safe, reasoning


def parse_command_response(text: str) -> ParsedCommand:
    """Parse a command response from the LLM.
    
    Args:
        text: The LLM response text.
        
    Returns:
        Parsed command information.
    """
    command = extract_command(text)
    is_safe, safety_reasoning = parse_safety_assessment(text)
    
    # Extract explanation (text before the command)
    explanation = text
    if command:
        parts = text.split("```", 1)
        if len(parts) > 1:
            explanation = parts[0].strip()
    
    return ParsedCommand(
        command=command or "",
        explanation=explanation,
        is_safe=is_safe,
        safety_reasoning=safety_reasoning
    )


def parse_analysis_response(text: str) -> ParsedAnalysis:
    """Parse an analysis response from the LLM.
    
    Args:
        text: The LLM response text.
        
    Returns:
        Parsed analysis information.
    """
    # Extract summary (first paragraph)
    paragraphs = [p.strip() for p in text.split("\n\n")]
    summary = paragraphs[0] if paragraphs else ""
    
    # Check for errors and warnings
    lower_text = text.lower()
    errors_detected = any(phrase in lower_text for phrase in ["error", "exception", "failed", "failure"])
    warnings_detected = any(phrase in lower_text for phrase in ["warning", "caution", "attention"])
    
    # Extract key points and next steps
    key_points = []
    next_steps = []
    
    # Look for numbered or bulleted lists
    list_pattern = r"(?:^|\n)(?:\d+\.|\*|\-)\s+(.*?)(?=(?:\n(?:\d+\.|\*|\-)|$))"
    list_items = re.findall(list_pattern, text, re.DOTALL)
    
    for item in list_items:
        item = item.strip()
        if "next" in item.lower() or "should" in item.lower() or "recommend" in item.lower():
            next_steps.append(item)
        else:
            key_points.append(item)
    
    return ParsedAnalysis(
        summary=summary,
        errors_detected=errors_detected,
        warnings_detected=warnings_detected,
        key_points=key_points,
        next_steps=next_steps
    )


def parse_response(text: str) -> ParsedResponse:
    """Parse a response from the LLM.
    
    Args:
        text: The LLM response text.
        
    Returns:
        Parsed response with type and content.
    """
    # Determine the type of response
    lower_text = text.lower()
    
    if extract_command(text) and ("execute" in lower_text or "run" in lower_text):
        # This is likely a command response
        response_type = ResponseType.COMMAND
        command = parse_command_response(text)
        return ParsedResponse(
            type=response_type,
            content=text,
            command=command
        )
    elif "output" in lower_text and any(word in lower_text for word in ["analysis", "result", "mean"]):
        # This is likely an analysis response
        response_type = ResponseType.ANALYSIS
        analysis = parse_analysis_response(text)
        return ParsedResponse(
            type=response_type,
            content=text,
            analysis=analysis
        )
    elif "error" in lower_text and any(word in lower_text for word in ["fix", "resolve", "handle"]):
        # This is likely an error handling response
        response_type = ResponseType.ERROR
        return ParsedResponse(
            type=response_type,
            content=text
        )
    else:
        # General response
        return ParsedResponse(
            type=ResponseType.GENERAL,
            content=text
        )
