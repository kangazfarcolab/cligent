"""
Security module for command validation and safety checks.
This module provides functionality for validating commands and ensuring they are safe to execute.
"""

import os
import re
import shlex
from typing import Dict, List, Optional, Tuple, Set, Pattern
from dataclasses import dataclass, field


@dataclass
class SecurityRule:
    """Rule for command security validation."""
    
    pattern: str
    description: str
    is_regex: bool = False
    
    _compiled_regex: Optional[Pattern] = None
    
    def __post_init__(self):
        """Initialize the rule after creation."""
        if self.is_regex:
            self._compiled_regex = re.compile(self.pattern)
    
    def matches(self, command: str) -> bool:
        """Check if the command matches this rule.
        
        Args:
            command: The command to check.
            
        Returns:
            True if the command matches this rule, False otherwise.
        """
        if self.is_regex:
            return bool(self._compiled_regex.search(command))
        else:
            return command.strip().startswith(self.pattern)


@dataclass
class SecurityPolicy:
    """Security policy for command execution."""
    
    # Lists of allowed and denied commands/patterns
    allowed_commands: List[SecurityRule] = field(default_factory=list)
    denied_commands: List[SecurityRule] = field(default_factory=list)
    
    # Restricted directories that cannot be accessed
    restricted_dirs: List[str] = field(default_factory=list)
    
    # Maximum allowed command length
    max_command_length: int = 1000
    
    # Whether to allow potentially destructive file operations
    allow_file_deletion: bool = False
    allow_file_overwrite: bool = True
    
    # Whether to allow network access
    allow_network_access: bool = True
    
    @classmethod
    def default_policy(cls) -> "SecurityPolicy":
        """Create a default security policy with reasonable restrictions."""
        return cls(
            denied_commands=[
                SecurityRule("rm -rf /", "Delete root directory"),
                SecurityRule("rm -rf /*", "Delete all files in root"),
                SecurityRule("sudo", "Superuser execution"),
                SecurityRule("su", "Switch user"),
                SecurityRule("dd", "Disk operations"),
                SecurityRule("mkfs", "Format filesystem"),
                SecurityRule("mv /* ", "Move files from root"),
                SecurityRule(">(.*)/dev/", "Redirect to device files", is_regex=True),
                SecurityRule("chmod -R 777 /", "Change permissions recursively on root"),
                SecurityRule(":(){:|:&};:", "Fork bomb"),
            ],
            restricted_dirs=[
                "/etc/",
                "/var/",
                "/boot/",
                "/root/",
                "/proc/",
                "/sys/",
            ],
            allow_file_deletion=False,
            allow_network_access=True,
        )


class SecurityValidator:
    """Validator for command security."""
    
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        """Initialize the security validator.
        
        Args:
            policy: Security policy to use. If None, uses the default policy.
        """
        self.policy = policy or SecurityPolicy.default_policy()
    
    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Validate a command against the security policy.
        
        Args:
            command: The command to validate.
            
        Returns:
            Tuple of (is_valid, reason). If is_valid is False, reason contains
            the reason why the command is not valid.
        """
        # Check command length
        if len(command) > self.policy.max_command_length:
            return False, f"Command exceeds maximum length of {self.policy.max_command_length} characters"
        
        # Check for denied commands
        for rule in self.policy.denied_commands:
            if rule.matches(command):
                return False, f"Command matches denied pattern: {rule.description}"
        
        # Check for allowed commands if specified
        if self.policy.allowed_commands:
            is_allowed = False
            for rule in self.policy.allowed_commands:
                if rule.matches(command):
                    is_allowed = True
                    break
            
            if not is_allowed:
                return False, "Command does not match any allowed patterns"
        
        # Check for restricted directories
        for restricted_dir in self.policy.restricted_dirs:
            if restricted_dir in command:
                return False, f"Command attempts to access restricted directory: {restricted_dir}"
        
        # Check for file deletion if not allowed
        if not self.policy.allow_file_deletion:
            if re.search(r"\brm\b", command) and not re.search(r"\brm\b.*-r", command):
                return False, "File deletion is not allowed"
            if re.search(r"\brm\b.*-r", command) or re.search(r"\brm\b.*-rf", command):
                return False, "Recursive file deletion is not allowed"
        
        # Check for network access if not allowed
        if not self.policy.allow_network_access:
            network_commands = ["curl", "wget", "nc", "netcat", "ssh", "scp", "ftp", "telnet"]
            for net_cmd in network_commands:
                if re.search(rf"\b{net_cmd}\b", command):
                    return False, "Network access is not allowed"
        
        return True, None
    
    def sanitize_command(self, command: str) -> str:
        """Sanitize a command to make it safer.
        
        This method attempts to modify the command to make it safer,
        such as by adding safeguards or removing dangerous options.
        
        Args:
            command: The command to sanitize.
            
        Returns:
            The sanitized command.
        """
        # Parse the command into tokens
        try:
            tokens = shlex.split(command)
        except:
            # If parsing fails, return the original command
            return command
        
        if not tokens:
            return command
        
        # Get the base command
        base_cmd = tokens[0]
        
        # Apply command-specific sanitization
        if base_cmd == "rm":
            # Add -i flag for interactive deletion if not already present
            if "-i" not in tokens and not self.policy.allow_file_deletion:
                tokens.insert(1, "-i")
            
            # Remove -f flag if present
            if "-f" in tokens:
                tokens.remove("-f")
            
            # Handle combined flags like -rf
            for i, token in enumerate(tokens):
                if token.startswith("-") and "f" in token:
                    tokens[i] = token.replace("f", "")
        
        # Reconstruct the command
        return shlex.join(tokens)
    
    def get_command_risk_level(self, command: str) -> Tuple[str, str]:
        """Assess the risk level of a command.
        
        Args:
            command: The command to assess.
            
        Returns:
            Tuple of (risk_level, explanation) where risk_level is one of:
            "low", "medium", "high", "critical"
        """
        # Default risk level
        risk_level = "low"
        explanation = "Command appears to be safe."
        
        # Check for high-risk commands
        high_risk_patterns = [
            (r"\brm\b.*-r", "high", "Recursive file deletion"),
            (r"\bchmod\b.*-R", "high", "Recursive permission changes"),
            (r"\bchown\b.*-R", "high", "Recursive ownership changes"),
            (r">(.*)/dev/", "medium", "Writing to device files"),
            (r"\bmv\b", "medium", "Moving files"),
            (r"\bcp\b", "low", "Copying files"),
            (r"\bsudo\b", "critical", "Superuser execution"),
            (r"\bsu\b", "critical", "User switching"),
            (r"\bdd\b", "high", "Direct disk operations"),
            (r"\bmkfs\b", "critical", "Filesystem formatting"),
            (r"\bcurl\b.*\|\s*sh", "critical", "Piping web content to shell"),
            (r"\bwget\b.*\|\s*sh", "critical", "Piping web content to shell"),
        ]
        
        for pattern, level, reason in high_risk_patterns:
            if re.search(pattern, command):
                risk_level = level
                explanation = reason
                break
        
        return risk_level, explanation
