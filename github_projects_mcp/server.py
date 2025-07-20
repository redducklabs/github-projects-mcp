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
                token=config.github_token, max_retries=config.max_retries, retry_delay=config.retry_delay
            )
            logger.info("GitHub Projects client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise
    return github_client


@mcp.tool()
def list_accessible_projects(first: int = 20, after: Optional[str] = None) -> Dict[str, Any]:
    """List all projects accessible to the authenticated user with pagination support

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. For large datasets,
    use pagination with 'after' cursor from pageInfo.endCursor. Default 20 items is efficient
    for most use cases.

    CRITICAL: Check hasNextPage and paginate if needed for complete results.

    Args:
        first: Number of projects to retrieve (default: 20, max: 25)
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
        # Enforce reasonable pagination limit
        if first > 25:
            first = 25
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

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. Use pagination
    for large organizations with many projects.

    Args:
        org_login: Organization login name
        first: Number of projects to retrieve (default: 20, max: 25)
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

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. Most users have
    few projects, so default 20 is usually sufficient.

    Args:
        user_login: User login name
        first: Number of projects to retrieve (default: 20, max: 25)
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
    For large projects (25+ items), consider using get_project_items_advanced() with
    custom_fields to select only needed data (e.g., 'id content { title }').

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. Projects can have
    1000+ items, requiring multiple paginated requests.

    CRITICAL: When counting items, you MUST paginate through ALL pages if hasNextPage=true.
    Single page results will be incomplete.

    Args:
        project_id: GitHub Project ID
        first: Number of items to retrieve (default: 50, max: 25)
        after: Cursor for pagination (optional)

    Returns:
        Dictionary with 'nodes' (list of items) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        # Enforce reasonable pagination limit
        if first > 25:
            first = 25
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
    custom_variables: Optional[str] = None,
) -> Dict[str, Any]:
    """Get project items with custom GraphQL modifiers for advanced use cases

    EFFICIENCY: Use custom_fields to dramatically reduce response size. Full item data
    can be 25KB+ for 20 items, but selective fields can reduce this to <1KB for 25+ items.

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. For counting/analysis
    use cases, use 'first: 25' and selective field queries with pagination.

    MILESTONE FIELDS: Use 'fieldValues(first:10)' to get milestone data. Only items with
    milestone fields will have the ProjectV2ItemFieldMilestoneValue data.

    CRITICAL: When counting by milestone, you MUST check ALL pages if hasNextPage=true.
    Single page counts will be incomplete for large projects.

    Args:
        project_id: GitHub Project ID
        first: Number of items to retrieve (default: 50, max: 25)
        after: Cursor for pagination (optional)
        custom_fields: Custom GraphQL field selection for efficiency (recommended)
        custom_filters: Custom GraphQL filters (limited GitHub API support)
        custom_variables: JSON string of custom variables (optional)

    Returns:
        Dictionary with 'nodes' (list of items) and 'pageInfo' (pagination info)

    EFFICIENCY EXAMPLES:
        # Get only milestone data for counting (reduces 25 items from ~6KB+ to ~300B):
        custom_fields = (
            "fieldValues(first:10) { nodes { ... on ProjectV2ItemFieldMilestoneValue { milestone { title } } } } "
            "content { ... on Issue { number } }"
        )

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

        # Enforce reasonable pagination limit
        if first > 25:
            first = 25

        return client.get_project_items_advanced(
            project_id, first, after, custom_fields, custom_filters, variables_dict
        )
    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


@mcp.tool()
def execute_custom_project_query(query: str, variables: Optional[str] = None) -> Dict[str, Any]:
    """Execute a custom GraphQL query for maximum flexibility

    SECURITY: This tool validates queries to prevent mutations and schema introspection.
    Only 'query' operations are allowed, not 'mutation' or 'subscription'.

    PAGINATION: Server limits pagination to 25 items per request for performance.
    Use 'first: 25' and cursor-based pagination for large datasets.

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
              items(first: 25, after: $after) {
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
def update_item_field_value(
    project_id: str, item_id: str, field_id: str, value: Union[str, float, Dict[str, Any]]
) -> Dict[str, Any]:
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
def update_project(
    project_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    readme: Optional[str] = None,
    public: Optional[bool] = None,
) -> Dict[str, Any]:
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


def _parse_search_filters(filters: Optional[str]) -> Dict[str, Any]:
    """Parse JSON filters for search."""
    filters_dict = {}
    if filters:
        import json
        try:
            filters_dict = json.loads(filters)
        except json.JSONDecodeError:
            raise Exception("Invalid JSON in filters parameter")
    return filters_dict


def _build_search_query() -> str:
    """Build GraphQL query for searching project items."""
    return """
    query SearchProjectItems($id: ID!, $first: Int!, $after: String) {
      node(id: $id) {
        ... on ProjectV2 {
          items(first: $first, after: $after) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              content {
                ... on Issue {
                  id
                  title
                  body
                  issueState: state
                  number
                  url
                }
                ... on PullRequest {
                  id
                  title
                  body
                  prState: state
                  number
                  url
                }
                ... on DraftIssue {
                  id
                  title
                  body
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldTextValue {
                    text
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldNumberValue {
                    number
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """


def _matches_content_search(item: Dict[str, Any], query_lower: str) -> bool:
    """Check if item content matches the search query."""
    if not item.get("content"):
        return False

    content = item["content"]
    title = content.get("title", "").lower()
    body = content.get("body", "").lower()

    return query_lower in title or query_lower in body


def _matches_field_search(item: Dict[str, Any], query_lower: str) -> bool:
    """Check if item field values match the search query."""
    if not item.get("fieldValues", {}).get("nodes"):
        return False

    for field_value in item["fieldValues"]["nodes"]:
        if field_value.get("text") and query_lower in field_value["text"].lower():
            return True
        elif field_value.get("name") and query_lower in field_value["name"].lower():
            return True
    return False


def _apply_search_filters(item: Dict[str, Any], filters_dict: Dict[str, Any]) -> bool:
    """Apply additional filters to search results."""
    if not filters_dict:
        return True

    # Example filter: {"state": "OPEN", "field_name": "value"}
    if "state" in filters_dict:
        content = item.get("content", {})
        if content.get("state") != filters_dict["state"]:
            return False

    # Add more filter logic as needed
    return True


@mcp.tool()
def search_project_items(project_id: str, query: str, filters: Optional[str] = None) -> Dict[str, Any]:
    """Search items by content/fields within a project

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. For large projects,
    use pagination with 'after' cursor from pageInfo.endCursor.

    CRITICAL: When searching large projects, you MUST paginate through ALL pages if hasNextPage=true.
    Single page results will be incomplete.

    Args:
        project_id: GitHub Project ID
        query: Search query string (searches in item content like title, body)
        filters: Optional JSON string with additional filters (e.g., field values, states)

    Returns:
        Dictionary with 'nodes' (list of matching items) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        filters_dict = _parse_search_filters(filters)
        graphql_query = _build_search_query()

        variables = {"id": project_id, "first": 25, "after": None}
        result = client._execute_with_retry(graphql_query, variables)

        if not result.get("node"):
            raise Exception("Project not found")

        items_data = result["node"]["items"]
        all_items = items_data["nodes"]

        # Client-side filtering based on query and filters
        filtered_items = []
        query_lower = query.lower()

        for item in all_items:
            # Check if item matches search criteria
            content_match = _matches_content_search(item, query_lower)
            field_match = not content_match and _matches_field_search(item, query_lower)

            if content_match or field_match:
                # Apply additional filters if provided
                if _apply_search_filters(item, filters_dict):
                    filtered_items.append(item)

        return {
            "nodes": filtered_items,
            "pageInfo": items_data["pageInfo"],
            "totalMatches": len(filtered_items)
        }

    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


def _build_field_value_query() -> str:
    """Build GraphQL query for getting items with field values."""
    return """
    query GetItemsByFieldValue($id: ID!, $first: Int!, $after: String) {
      node(id: $id) {
        ... on ProjectV2 {
          items(first: $first, after: $after) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              content {
                ... on Issue {
                  id
                  title
                  issueState: state
                  number
                  url
                }
                ... on PullRequest {
                  id
                  title
                  prState: state
                  number
                  url
                }
                ... on DraftIssue {
                  id
                  title
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldTextValue {
                    text
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldMultiSelectValue {
                    names
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldNumberValue {
                    number
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """


def _check_field_value_match(field_value: Dict[str, Any], target_value: str) -> bool:
    """Check if a field value matches the target value."""
    if "text" in field_value and field_value["text"] == target_value:
        return True
    elif "name" in field_value and field_value["name"] == target_value:
        return True
    elif "names" in field_value and target_value in field_value["names"]:
        return True
    elif "number" in field_value and str(field_value["number"]) == target_value:
        return True
    elif "date" in field_value and field_value["date"] == target_value:
        return True
    return False


def _filter_items_by_field_value(items: List[Dict[str, Any]], field_id: str, value: str) -> List[Dict[str, Any]]:
    """Filter items by specific field value."""
    filtered_items = []

    for item in items:
        if item.get("fieldValues", {}).get("nodes"):
            for field_value in item["fieldValues"]["nodes"]:
                field_info = field_value.get("field", {})

                if field_info.get("id") == field_id:
                    if _check_field_value_match(field_value, value):
                        filtered_items.append(item)
                        break

    return filtered_items


@mcp.tool()
def get_items_by_field_value(project_id: str, field_id: str, value: str) -> Dict[str, Any]:
    """Filter items by specific field values within a project

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. For large projects,
    use pagination with 'after' cursor from pageInfo.endCursor.

    CRITICAL: When filtering large projects, you MUST paginate through ALL pages if hasNextPage=true.
    Single page results will be incomplete.

    Args:
        project_id: GitHub Project ID
        field_id: Project field ID to filter by
        value: Field value to match

    Returns:
        Dictionary with 'nodes' (list of matching items) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        graphql_query = _build_field_value_query()

        variables = {"id": project_id, "first": 25, "after": None}
        result = client._execute_with_retry(graphql_query, variables)

        if not result.get("node"):
            raise Exception("Project not found")

        items_data = result["node"]["items"]
        all_items = items_data["nodes"]

        # Filter items by field value
        filtered_items = _filter_items_by_field_value(all_items, field_id, value)

        return {
            "nodes": filtered_items,
            "pageInfo": items_data["pageInfo"],
            "totalMatches": len(filtered_items)
        }

    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


def _build_milestone_query() -> str:
    """Build GraphQL query for getting items with milestone data."""
    return """
    query GetItemsByMilestone($id: ID!, $first: Int!, $after: String) {
      node(id: $id) {
        ... on ProjectV2 {
          items(first: $first, after: $after) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              content {
                ... on Issue {
                  id
                  title
                  issueState: state
                  number
                  url
                  milestone {
                    title
                  }
                }
                ... on PullRequest {
                  id
                  title
                  prState: state
                  number
                  url
                  milestone {
                    title
                  }
                }
                ... on DraftIssue {
                  id
                  title
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldMilestoneValue {
                    milestone {
                      title
                    }
                    field {
                      ... on ProjectV2FieldCommon {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """


def _check_content_milestone(item: Dict[str, Any], milestone_name: str) -> bool:
    """Check if item's content milestone matches the target milestone."""
    return item.get("content", {}).get("milestone", {}).get("title") == milestone_name


def _check_field_milestone(item: Dict[str, Any], milestone_name: str) -> bool:
    """Check if item's field values contain matching milestone."""
    if not item.get("fieldValues", {}).get("nodes"):
        return False

    for field_value in item["fieldValues"]["nodes"]:
        if "milestone" in field_value:
            milestone_info = field_value["milestone"]
            if milestone_info and milestone_info.get("title") == milestone_name:
                return True
    return False


def _filter_items_by_milestone(items: List[Dict[str, Any]], milestone_name: str) -> List[Dict[str, Any]]:
    """Filter items by milestone name."""
    filtered_items = []

    for item in items:
        content_match = _check_content_milestone(item, milestone_name)
        field_match = not content_match and _check_field_milestone(item, milestone_name)

        if content_match or field_match:
            filtered_items.append(item)

    return filtered_items


@mcp.tool()
def get_items_by_milestone(project_id: str, milestone_name: str) -> Dict[str, Any]:
    """Get items in a specific milestone within a project

    PAGINATION LIMITS: Server limits requests to max 25 items per request for performance. For large projects,
    use pagination with 'after' cursor from pageInfo.endCursor.

    CRITICAL: When filtering large projects, you MUST paginate through ALL pages if hasNextPage=true.
    Single page results will be incomplete.

    Args:
        project_id: GitHub Project ID
        milestone_name: Name of the milestone to filter by

    Returns:
        Dictionary with 'nodes' (list of items in milestone) and 'pageInfo' (pagination info)
    """
    try:
        client = get_github_client()
        graphql_query = _build_milestone_query()

        variables = {"id": project_id, "first": 25, "after": None}
        result = client._execute_with_retry(graphql_query, variables)

        if not result.get("node"):
            raise Exception("Project not found")

        items_data = result["node"]["items"]
        all_items = items_data["nodes"]

        # Filter items by milestone
        filtered_items = _filter_items_by_milestone(all_items, milestone_name)

        return {
            "nodes": filtered_items,
            "pageInfo": items_data["pageInfo"],
            "totalMatches": len(filtered_items)
        }

    except (GitHubAPIError, RateLimitError) as e:
        raise Exception(f"GitHub API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


def main() -> None:
    """Main entry point for the MCP server"""
    try:
        # For FastMCP, we just run the server directly
        mcp.run()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
