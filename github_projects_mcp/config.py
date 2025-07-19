"""Configuration management for GitHub Projects MCP Server"""

import os
from typing import Optional


class Config:
    """Configuration class for environment variables"""
    
    def __init__(self):
        self.github_token: str = self._get_required_env("GITHUB_TOKEN")
        self.max_retries: int = int(os.getenv("GITHUB_API_MAX_RETRIES", "3"))
        self.retry_delay: int = int(os.getenv("GITHUB_API_RETRY_DELAY", "60"))
        self.transport: str = os.getenv("MCP_TRANSPORT", "stdio").lower()
        self.host: str = os.getenv("MCP_HOST", "localhost")
        self.port: int = int(os.getenv("MCP_PORT", "8000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def validate_transport(self) -> None:
        """Validate transport configuration"""
        valid_transports = ["stdio", "sse", "http"]
        if self.transport not in valid_transports:
            raise ValueError(f"Invalid transport '{self.transport}'. Must be one of: {valid_transports}")


# Global config instance
config = Config()