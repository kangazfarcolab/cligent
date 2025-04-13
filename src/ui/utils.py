"""
UI utilities for the CLI agent.
This module provides utility functions for the CLI interface.
"""

import re
from typing import List, Tuple, Optional


def extract_code_blocks(text: str) -> List[Tuple[str, Optional[str]]]:
    """Extract code blocks from markdown text.
    
    Args:
        text: The text containing markdown code blocks.
        
    Returns:
        List of tuples (code, language) where language may be None.
    """
    # Match code blocks with triple backticks and optional language
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    # Process matches
    result = []
    for lang, code in matches:
        result.append((code.strip(), lang if lang else None))
    
    return result


def extract_command(text: str) -> Optional[str]:
    """Extract a command from text.
    
    Args:
        text: The text containing a command.
        
    Returns:
        The extracted command, or None if no command is found.
    """
    # Look for lines that look like commands
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("$") or line.startswith(">"):
            return line[1:].strip()
    
    # If no command-like lines, look for the first non-empty line
    for line in lines:
        line = line.strip()
        if line:
            return line
    
    return None
