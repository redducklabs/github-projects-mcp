"""GitHub Projects MCP Server"""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mcp.server import stdio, sse, streamable_http
from mcp.types import Resource, Tool

from .config import config
from .core.client import GitHubProjectsClient
from .core.models import GitHubAPIError, RateLimitError

# Configure logging
logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("GitHub Projects")

# Initialize GitHub client
try:
    github_client = GitHubProjectsClient(
        token=config.github_token,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay
    )
    logger.info("GitHub Projects client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize GitHub client: {e}")
    sys.exit(1)


@mcp.tool()
def get_organization_projects(org_login: str, first: int = 20) -> List[Dict[str, Any]]:
    """Get projects for an organization
    
    Args:
        org_login: Organization login name
        first: Number of projects to retrieve (default: 20)
    
    Returns:
        List of project data
    """
    try:
        return github_client.get_organization_projects(org_login, first)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_user_projects(user_login: str, first: int = 20) -> List[Dict[str, Any]]:
    """Get projects for a user
    
    Args:
        user_login: User login name
        first: Number of projects to retrieve (default: 20)
    
    Returns:
        List of project data
    """
    try:
        return github_client.get_user_projects(user_login, first)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_project(project_id: str) -> Dict[str, Any]:
    """Get a specific project by ID
    
    Args:
        project_id: GitHub Project ID
    
    Returns:
        Project data
    """
    try:
        return github_client.get_project(project_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_project_items(project_id: str, first: int = 50) -> List[Dict[str, Any]]:
    """Get items in a project
    
    Args:
        project_id: GitHub Project ID
        first: Number of items to retrieve (default: 50)
    
    Returns:
        List of project items
    """
    try:
        return github_client.get_project_items(project_id, first)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_project_fields(project_id: str) -> List[Dict[str, Any]]:
    """Get fields in a project
    
    Args:
        project_id: GitHub Project ID
    
    Returns:
        List of project fields
    """
    try:
        return github_client.get_project_fields(project_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def add_item_to_project(project_id: str, content_id: str) -> Dict[str, Any]:
    """Add an item to a project
    
    Args:
        project_id: GitHub Project ID
        content_id: ID of the content to add (issue, PR, etc.)
    
    Returns:
        Added item data
    """
    try:
        return github_client.add_item_to_project(project_id, content_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def update_item_field_value(project_id: str, item_id: str, field_id: str, value: Union[str, float, Dict[str, Any]]) -> Dict[str, Any]:
    """Update a field value for a project item
    
    Args:
        project_id: GitHub Project ID
        item_id: Project item ID
        field_id: Field ID to update
        value: New field value
    
    Returns:
        Updated item data
    """
    try:
        return github_client.update_item_field_value(project_id, item_id, field_id, value)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def remove_item_from_project(project_id: str, item_id: str) -> Dict[str, Any]:
    """Remove an item from a project
    
    Args:
        project_id: GitHub Project ID
        item_id: Project item ID to remove
    
    Returns:
        Deletion confirmation
    """
    try:
        return github_client.remove_item_from_project(project_id, item_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def archive_item(project_id: str, item_id: str) -> Dict[str, Any]:
    """Archive an item in a project
    
    Args:
        project_id: GitHub Project ID
        item_id: Project item ID to archive
    
    Returns:
        Archived item data
    """
    try:
        return github_client.archive_item(project_id, item_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def create_project(owner_id: str, title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new project
    
    Args:
        owner_id: ID of the owner (organization or user)
        title: Project title
        description: Optional project description
    
    Returns:
        Created project data
    """
    try:
        return github_client.create_project(owner_id, title, description)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def update_project(project_id: str, title: Optional[str] = None, description: Optional[str] = None, 
                  readme: Optional[str] = None, public: Optional[bool] = None) -> Dict[str, Any]:
    """Update a project
    
    Args:
        project_id: GitHub Project ID
        title: New project title (optional)
        description: New project description (optional)
        readme: New project readme (optional)
        public: Whether project should be public (optional)
    
    Returns:
        Updated project data
    """
    try:
        return github_client.update_project(project_id, title, description, readme, public)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete a project
    
    Args:
        project_id: GitHub Project ID to delete
    
    Returns:
        Deletion confirmation
    """
    try:
        return github_client.delete_project(project_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


async def main():
    """Main entry point for the MCP server"""
    try:
        # Validate configuration
        config.validate_transport()
        
        if config.transport == "stdio":
            async with stdio.stdio_server() as (read_stream, write_stream):
                await mcp.run(read_stream, write_stream, mcp.create_initialization_options())
        elif config.transport == "sse":
            await sse.run_sse_server(mcp, config.host, config.port)
        elif config.transport == "http":
            await streamable_http.run_streamable_http_server(mcp, config.host, config.port)
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")
            
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())