"""Configuration management for GitHub Projects MCP Server"""

import os
from typing import Optional


class Config:
    """Configuration class for environment variables"""
    
    def __init__(self):
        self._github_token: Optional[str] = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of config values"""
        if not self._initialized:
            # Set transport and other non-critical config first
            self._max_retries: int = int(os.getenv("GITHUB_API_MAX_RETRIES", "3"))
            self._retry_delay: int = int(os.getenv("GITHUB_API_RETRY_DELAY", "60"))
            self._transport: str = os.getenv("MCP_TRANSPORT", "stdio").lower()
            self._host: str = os.getenv("MCP_HOST", "localhost")
            self._port: int = int(os.getenv("MCP_PORT", "8000"))
            self._log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
            self._initialized = True
            
    def _ensure_github_token(self):
        """Lazy initialization of GitHub token (separate from other config)"""
        if self._github_token is None:
            self._github_token = self._get_required_env("GITHUB_TOKEN")
    
    @property
    def github_token(self) -> str:
        """Get GitHub token, loading config if needed"""
        self._ensure_github_token()
        return self._github_token
        
    @property 
    def transport(self) -> str:
        """Get transport mode"""
        self._ensure_initialized()
        return self._transport
    
    @transport.setter
    def transport(self, value: str):
        """Set transport mode"""
        self._transport = value
        
    @property
    def log_level(self) -> str:
        """Get log level"""
        self._ensure_initialized()
        return self._log_level
        
    @property
    def max_retries(self) -> int:
        """Get max retries"""
        self._ensure_initialized()
        return self._max_retries
        
    @property
    def retry_delay(self) -> int:
        """Get retry delay"""
        self._ensure_initialized()
        return self._retry_delay
        
    @property
    def host(self) -> str:
        """Get host"""
        self._ensure_initialized()
        return self._host
        
    @property
    def port(self) -> int:
        """Get port"""
        self._ensure_initialized()
        return self._port
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def validate_transport(self) -> None:
        """Validate transport configuration"""
        self._ensure_initialized()
        valid_transports = ["stdio", "sse", "http"]
        if self.transport not in valid_transports:
            raise ValueError(f"Invalid transport '{self.transport}'. Must be one of: {valid_transports}")


# Global config instance
config = Config()