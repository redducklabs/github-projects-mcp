"""Test configuration and fixtures"""

import os
import pytest
import asyncio
from typing import Generator, Dict, Any
from dotenv import load_dotenv

from github_projects_mcp.core.client import GitHubProjectsClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Load test configuration from environment"""
    # Load test environment variables
    load_dotenv(".env.test", override=True)
    
    required_vars = [
        "TEST_GITHUB_TOKEN",
        "TEST_ORG_NAME", 
        "TEST_PROJECT_ID",
        "TEST_REPO_OWNER",
        "TEST_REPO_NAME"
    ]
    
    config = {}
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        config[var.lower()] = value
    
    if missing:
        pytest.skip(f"Required test environment variables not set: {missing}")
    
    return config


@pytest.fixture(scope="session")
def github_client(test_config: Dict[str, Any]) -> GitHubProjectsClient:
    """Create GitHub client for testing"""
    return GitHubProjectsClient(
        token=test_config["test_github_token"],
        max_retries=1,  # Faster failure for tests
        retry_delay=1   # Shorter delay for tests
    )


@pytest.fixture
def test_issue_data() -> Dict[str, Any]:
    """Sample issue data for testing"""
    return {
        "title": "Test Issue for MCP Server",
        "body": "This is a test issue created by the GitHub Projects MCP Server test suite."
    }