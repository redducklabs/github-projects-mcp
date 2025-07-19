"""GitHub Projects GraphQL API client"""

import os
import time
from typing import Any, Dict, List, Optional, Union
import logging

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .models import (
    GitHubAPIError, 
    RateLimitError,
    ProjectV2,
    ProjectV2Item,
    ProjectV2Field,
    ProjectV2ItemFieldValue
)

logger = logging.getLogger(__name__)


class GitHubProjectsClient:
    """Client for interacting with GitHub Projects GraphQL API"""
    
    def __init__(self, token: str, max_retries: int = 3, retry_delay: int = 60):
        """Initialize the GitHub Projects client
        
        Args:
            token: GitHub Personal Access Token
            max_retries: Maximum number of retries for rate limit errors
            retry_delay: Delay in seconds between retries
        """
        self.token = token
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        transport = RequestsHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
    
    def _execute_with_retry(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query with retry logic for rate limits"""
        for attempt in range(self.max_retries + 1):
            try:
                result = self.client.execute(gql(query), variable_values=variables)
                return result
            except Exception as e:
                if "rate limit" in str(e).lower() and attempt < self.max_retries:
                    logger.warning(f"Rate limit hit, retrying in {self.retry_delay} seconds (attempt {attempt + 1})")
                    time.sleep(self.retry_delay)
                    continue
                elif "rate limit" in str(e).lower():
                    raise RateLimitError()
                else:
                    # Parse GraphQL errors
                    error_msg = str(e)
                    if hasattr(e, 'response') and e.response:
                        status_code = getattr(e.response, 'status_code', None)
                        raise GitHubAPIError(error_msg, status_code)
                    raise GitHubAPIError(error_msg)
    
    def get_organization_projects(self, org_login: str, first: int = 20) -> List[Dict[str, Any]]:
        """Get projects for an organization"""
        query = """
        query GetOrgProjects($login: String!, $first: Int!) {
          organization(login: $login) {
            projectsV2(first: $first) {
              nodes {
                id
                title
                shortDescription
                readme
                public
                closed
                createdAt
                updatedAt
                number
                url
                owner {
                  ... on Organization {
                    login
                  }
                  ... on User {
                    login
                  }
                }
              }
            }
          }
        }
        """
        variables = {"login": org_login, "first": first}
        result = self._execute_with_retry(query, variables)
        return result["organization"]["projectsV2"]["nodes"]
    
    def get_user_projects(self, user_login: str, first: int = 20) -> List[Dict[str, Any]]:
        """Get projects for a user"""
        query = """
        query GetUserProjects($login: String!, $first: Int!) {
          user(login: $login) {
            projectsV2(first: $first) {
              nodes {
                id
                title
                shortDescription
                readme
                public
                closed
                createdAt
                updatedAt
                number
                url
                owner {
                  ... on Organization {
                    login
                  }
                  ... on User {
                    login
                  }
                }
              }
            }
          }
        }
        """
        variables = {"login": user_login, "first": first}
        result = self._execute_with_retry(query, variables)
        return result["user"]["projectsV2"]["nodes"]
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a specific project by ID"""
        query = """
        query GetProject($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              id
              title
              shortDescription
              readme
              public
              closed
              createdAt
              updatedAt
              number
              url
              owner {
                ... on Organization {
                  login
                }
                ... on User {
                  login
                }
              }
            }
          }
        }
        """
        variables = {"id": project_id}
        result = self._execute_with_retry(query, variables)
        return result["node"]
    
    def get_project_items(self, project_id: str, first: int = 50) -> List[Dict[str, Any]]:
        """Get items in a project"""
        query = """
        query GetProjectItems($id: ID!, $first: Int!) {
          node(id: $id) {
            ... on ProjectV2 {
              items(first: $first) {
                nodes {
                  id
                  type
                  createdAt
                  updatedAt
                  isArchived
                  content {
                    ... on Issue {
                      id
                      title
                      number
                      url
                      issueState: state
                    }
                    ... on PullRequest {
                      id
                      title
                      number
                      url
                      prState: state
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
                      ... on ProjectV2ItemFieldNumberValue {
                        number
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
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field {
                          ... on ProjectV2FieldCommon {
                            id
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldIterationValue {
                        title
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
        variables = {"id": project_id, "first": first}
        result = self._execute_with_retry(query, variables)
        return result["node"]["items"]["nodes"]
    
    def get_project_fields(self, project_id: str) -> List[Dict[str, Any]]:
        """Get fields in a project"""
        query = """
        query GetProjectFields($id: ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2Field {
                    id
                    name
                    dataType
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    dataType
                    options {
                      id
                      name
                    }
                  }
                  ... on ProjectV2IterationField {
                    id
                    name
                    dataType
                    configuration {
                      iterations {
                        id
                        title
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"id": project_id}
        result = self._execute_with_retry(query, variables)
        return result["node"]["fields"]["nodes"]
    
    def add_item_to_project(self, project_id: str, content_id: str) -> Dict[str, Any]:
        """Add an item to a project"""
        mutation = """
        mutation AddProjectItem($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {
            projectId: $projectId
            contentId: $contentId
          }) {
            item {
              id
            }
          }
        }
        """
        variables = {"projectId": project_id, "contentId": content_id}
        result = self._execute_with_retry(mutation, variables)
        return result["addProjectV2ItemById"]["item"]
    
    def update_item_field_value(self, project_id: str, item_id: str, field_id: str, value: Union[str, float, Dict[str, Any]]) -> Dict[str, Any]:
        """Update a field value for a project item"""
        mutation = """
        mutation UpdateProjectItemField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValueInput!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: $value
          }) {
            projectV2Item {
              id
            }
          }
        }
        """
        
        # Format value based on type
        if isinstance(value, str):
            formatted_value = {"text": value}
        elif isinstance(value, (int, float)):
            formatted_value = {"number": value}
        elif isinstance(value, dict):
            formatted_value = value
        else:
            formatted_value = {"text": str(value)}
        
        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": formatted_value
        }
        result = self._execute_with_retry(mutation, variables)
        return result["updateProjectV2ItemFieldValue"]["projectV2Item"]
    
    def remove_item_from_project(self, project_id: str, item_id: str) -> Dict[str, Any]:
        """Remove an item from a project"""
        mutation = """
        mutation RemoveProjectItem($projectId: ID!, $itemId: ID!) {
          deleteProjectV2Item(input: {
            projectId: $projectId
            itemId: $itemId
          }) {
            deletedItemId
          }
        }
        """
        variables = {"projectId": project_id, "itemId": item_id}
        result = self._execute_with_retry(mutation, variables)
        return result["deleteProjectV2Item"]
    
    def archive_item(self, project_id: str, item_id: str) -> Dict[str, Any]:
        """Archive an item in a project"""
        mutation = """
        mutation ArchiveProjectItem($projectId: ID!, $itemId: ID!) {
          archiveProjectV2Item(input: {
            projectId: $projectId
            itemId: $itemId
          }) {
            item {
              id
              isArchived
            }
          }
        }
        """
        variables = {"projectId": project_id, "itemId": item_id}
        result = self._execute_with_retry(mutation, variables)
        return result["archiveProjectV2Item"]["item"]
    
    def create_project(self, owner_id: str, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        mutation = """
        mutation CreateProject($ownerId: ID!, $title: String!, $description: String) {
          createProjectV2(input: {
            ownerId: $ownerId
            title: $title
            shortDescription: $description
          }) {
            projectV2 {
              id
              title
              shortDescription
              url
            }
          }
        }
        """
        variables = {"ownerId": owner_id, "title": title}
        if description:
            variables["description"] = description
        result = self._execute_with_retry(mutation, variables)
        return result["createProjectV2"]["projectV2"]
    
    def update_project(self, project_id: str, title: Optional[str] = None, description: Optional[str] = None, readme: Optional[str] = None, public: Optional[bool] = None) -> Dict[str, Any]:
        """Update a project"""
        mutation = """
        mutation UpdateProject($projectId: ID!, $title: String, $description: String, $readme: String, $public: Boolean) {
          updateProjectV2(input: {
            projectId: $projectId
            title: $title
            shortDescription: $description
            readme: $readme
            public: $public
          }) {
            projectV2 {
              id
              title
              shortDescription
              readme
              public
            }
          }
        }
        """
        variables = {"projectId": project_id}
        if title:
            variables["title"] = title
        if description:
            variables["description"] = description
        if readme:
            variables["readme"] = readme
        if public is not None:
            variables["public"] = public
        
        result = self._execute_with_retry(mutation, variables)
        return result["updateProjectV2"]["projectV2"]
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a project"""
        mutation = """
        mutation DeleteProject($projectId: ID!) {
          deleteProjectV2(input: {
            projectId: $projectId
          }) {
            projectV2 {
              id
            }
          }
        }
        """
        variables = {"projectId": project_id}
        result = self._execute_with_retry(mutation, variables)
        return result["deleteProjectV2"]["projectV2"]