"""GitHub Projects MCP Server"""

import logging
import sys
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from .config import config
from .core.client import GitHubProjectsClient
from .core.models import GitHubAPIError, RateLimitError

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, rely on system environment

# Initialize MCP server
mcp = FastMCP("GitHub Projects")

# GitHub client will be initialized lazily
github_client: Optional[GitHubProjectsClient] = None
logger = logging.getLogger(__name__)


def get_github_client() -> GitHubProjectsClient:
    """Get or create GitHub client instance"""
    global github_client
    if github_client is None:
        # Configure logging now that we have config
        logging.basicConfig(level=getattr(logging, config.log_level))
        
        try:
            github_client = GitHubProjectsClient(
                token=config.github_token,
                max_retries=config.max_retries,
                retry_delay=config.retry_delay
            )
            logger.info("GitHub Projects client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise
    return github_client


@mcp.tool()
def list_accessible_projects(first: int = 20, after: Optional[str] = None) -> Dict[str, Any]:
    """List all projects accessible to the authenticated user with pagination support
    
    PAGINATION LIMITS: GitHub API allows max 100 items per request. For large datasets,
    use pagination with 'after' cursor from pageInfo.endCursor. Default 20 items is efficient
    for most use cases.
    
    CRITICAL: Check hasNextPage and paginate if needed for complete results.
    
    Args:
        first: Number of projects to retrieve (default: 20, max: 100)
        after: Cursor for pagination (optional)
    
    Returns:
        Dictionary with 'nodes' (list of projects) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        # Get viewer (authenticated user) info and their projects
        query = """
        query GetViewerProjects($first: Int!, $after: String) {
          viewer {
            login
            projectsV2(first: $first, after: $after) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                title
                shortDescription
                readme
                url
                public
                createdAt
                updatedAt
                owner {
                  ... on User {
                    login
                  }
                  ... on Organization {
                    login
                  }
                }
              }
            }
          }
        }
        """
        # Enforce GitHub API pagination limit
        if first > 100:
            first = 100
        variables = {"first": first}
        if after:
            variables["after"] = after
        result = client._execute_with_retry(query, variables)
        
        return result["viewer"]["projectsV2"]
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


@mcp.tool()
def get_organization_projects(org_login: str, first: int = 20, after: Optional[str] = None) -> Dict[str, Any]:
    """Get projects for an organization with pagination support
    
    PAGINATION LIMITS: GitHub API allows max 100 items per request. Use pagination
    for large organizations with many projects.
    
    Args:
        org_login: Organization login name
        first: Number of projects to retrieve (default: 20, max: 100)
        after: Cursor for pagination (optional)
    
    Returns:
        Dictionary with 'nodes' (list of projects) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        return client.get_organization_projects(org_login, first, after)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_user_projects(user_login: str, first: int = 20, after: Optional[str] = None) -> Dict[str, Any]:
    """Get projects for a user with pagination support
    
    PAGINATION LIMITS: GitHub API allows max 100 items per request. Most users have
    few projects, so default 20 is usually sufficient.
    
    Args:
        user_login: User login name
        first: Number of projects to retrieve (default: 20, max: 100)
        after: Cursor for pagination (optional)
    
    Returns:
        Dictionary with 'nodes' (list of projects) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        return client.get_user_projects(user_login, first, after)
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
        client = get_github_client()
        return client.get_project(project_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_project_items(project_id: str, first: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    """Get items in a project with pagination support
    
    EFFICIENCY WARNING: This returns FULL item data which can be 25KB+ for just 20 items.
    For large projects (100+ items), consider using get_project_items_advanced() with
    custom_fields to select only needed data (e.g., 'id content { title }').
    
    PAGINATION LIMITS: GitHub API allows max 100 items per request. Projects can have
    1000+ items, requiring multiple paginated requests.
    
    CRITICAL: When counting items, you MUST paginate through ALL pages if hasNextPage=true.
    Single page results will be incomplete.
    
    Args:
        project_id: GitHub Project ID
        first: Number of items to retrieve (default: 50, max: 100)
        after: Cursor for pagination (optional)
    
    Returns:
        Dictionary with 'nodes' (list of items) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        # Enforce GitHub API pagination limit
        if first > 100:
            first = 100
        return client.get_project_items(project_id, first, after)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


@mcp.tool()
def get_project_items_advanced(
    project_id: str, 
    first: int = 50, 
    after: Optional[str] = None,
    custom_fields: Optional[str] = None,
    custom_filters: Optional[str] = None,
    custom_variables: Optional[str] = None
) -> Dict[str, Any]:
    """Get project items with custom GraphQL modifiers for advanced use cases
    
    EFFICIENCY: Use custom_fields to dramatically reduce response size. Full item data
    can be 25KB+ for 20 items, but selective fields can reduce this to <1KB for 100+ items.
    
    PAGINATION LIMITS: GitHub API allows max 100 items per request. For counting/analysis
    use cases, increase 'first' to 100 and use selective field queries.
    
    MILESTONE FIELDS: Use 'fieldValues(first:10)' to get milestone data. Only items with
    milestone fields will have the ProjectV2ItemFieldMilestoneValue data.
    
    CRITICAL: When counting by milestone, you MUST check ALL pages if hasNextPage=true.
    Single page counts will be incomplete for large projects.
    
    Args:
        project_id: GitHub Project ID
        first: Number of items to retrieve (default: 50, max: 100)
        after: Cursor for pagination (optional)
        custom_fields: Custom GraphQL field selection for efficiency (recommended)
        custom_filters: Custom GraphQL filters (limited GitHub API support)
        custom_variables: JSON string of custom variables (optional)
    
    Returns:
        Dictionary with 'nodes' (list of items) and 'pageInfo' (pagination info)
        
    EFFICIENCY EXAMPLES:
        # Get only milestone data for counting (reduces 100 items from 25KB+ to ~1KB):
        custom_fields = "fieldValues(first:10) { nodes { ... on ProjectV2ItemFieldMilestoneValue { milestone { title } } } } content { ... on Issue { number } }"
        
        # Get minimal item data for browsing:
        custom_fields = "id content { title }"
        
        # Get issue/PR state with minimal data:
        custom_fields = "id content { ... on Issue { title state } ... on PullRequest { title state } }"
    """
    try:
        client = get_github_client()
        
        # Parse custom variables if provided
        variables_dict = None
        if custom_variables:
            import json
            try:
                variables_dict = json.loads(custom_variables)
            except json.JSONDecodeError:
                raise Exception("Invalid JSON in custom_variables parameter")
        
        # Enforce GitHub API pagination limit
        if first > 100:
            first = 100
            
        return client.get_project_items_advanced(
            project_id, first, after, custom_fields, custom_filters, variables_dict
        )
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


@mcp.tool()
def execute_custom_project_query(
    query: str,
    variables: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a custom GraphQL query for maximum flexibility
    
    SECURITY: This tool validates queries to prevent mutations and schema introspection.
    Only 'query' operations are allowed, not 'mutation' or 'subscription'.
    
    PAGINATION: Remember GitHub API limits pagination to 100 items per request.
    Use 'first: 100' and cursor-based pagination for large datasets.
    
    EFFICIENCY: Select only needed fields to reduce response size. Full project item
    data can exceed 25KB for just 20 items.
    
    CRITICAL: For counting, you MUST paginate through ALL results if hasNextPage=true.
    
    Args:
        query: Complete GraphQL query string (queries only, no mutations)
        variables: JSON string of query variables (optional)
    
    Returns:
        Raw GraphQL response data
        
    EFFICIENT EXAMPLES:
        # Count items by milestone (MUST paginate for complete count):
        query = '''
        query CountByMilestone($id: ID!, $after: String) {
          node(id: $id) {
            ... on ProjectV2 {
              items(first: 100, after: $after) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldMilestoneValue {
                        milestone { title }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        '''
        variables = '{"id": "PVT_kwDOCdCYe84A-G7b", "after": null}'
        
        # Get project total count only:
        query = '''
        query ProjectOverview($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              title
              items(first: 1) {
                totalCount
              }
            }
          }
        }
        '''
    """
    try:
        client = get_github_client()
        
        # Parse variables if provided
        variables_dict = {}
        if variables:
            import json
            try:
                variables_dict = json.loads(variables)
            except json.JSONDecodeError:
                raise Exception("Invalid JSON in variables parameter")
        
        return client.execute_custom_query(query, variables_dict)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


@mcp.tool()
def get_project_fields(project_id: str) -> List[Dict[str, Any]]:
    """Get fields in a project
    
    Args:
        project_id: GitHub Project ID
    
    Returns:
        List of project fields
    """
    try:
        client = get_github_client()
        return client.get_project_fields(project_id)
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
        client = get_github_client()
        return client.add_item_to_project(project_id, content_id)
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
        client = get_github_client()
        return client.update_item_field_value(project_id, item_id, field_id, value)
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
        client = get_github_client()
        return client.remove_item_from_project(project_id, item_id)
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
        client = get_github_client()
        return client.archive_item(project_id, item_id)
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
        client = get_github_client()
        return client.create_project(owner_id, title, description)
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
        client = get_github_client()
        return client.update_project(project_id, title, description, readme, public)
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
        client = get_github_client()
        return client.delete_project(project_id)
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")


def main():
    """Main entry point for the MCP server"""
    try:
        # For FastMCP, we just run the server directly
        mcp.run()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()