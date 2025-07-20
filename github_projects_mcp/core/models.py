"""Pydantic models for GitHub Projects API responses"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ProjectV2(BaseModel):
    """GitHub Project V2 model"""

    id: str
    title: str
    short_description: Optional[str] = None
    readme: Optional[str] = None
    public: bool
    closed: bool
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    number: int
    url: str
    owner: Dict[str, Any]


class ProjectV2Field(BaseModel):
    """GitHub Project V2 field model"""

    id: str
    name: str
    data_type: str = Field(alias="dataType")
    configuration: Optional[Dict[str, Any]] = None


class ProjectV2Item(BaseModel):
    """GitHub Project V2 item model"""

    id: str
    project: Dict[str, Any]
    content: Optional[Dict[str, Any]] = None
    type: str
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    is_archived: Optional[bool] = Field(alias="isArchived", default=None)


class ProjectV2ItemFieldValue(BaseModel):
    """GitHub Project V2 item field value model"""

    field: Dict[str, Any]
    value: Optional[Union[str, float, Dict[str, Any]]] = None


class ProjectsResponse(BaseModel):
    """Response model for projects queries"""

    projects_v2: Dict[str, Any] = Field(alias="projectsV2")


class OrganizationProjectsResponse(BaseModel):
    """Response model for organization projects"""

    organization: Dict[str, Any]


class UserProjectsResponse(BaseModel):
    """Response model for user projects"""

    user: Dict[str, Any]


class AddProjectV2ItemResponse(BaseModel):
    """Response model for adding project item"""

    add_project_v2_item_by_id: Dict[str, Any] = Field(alias="addProjectV2ItemById")


class UpdateProjectV2ItemFieldValueResponse(BaseModel):
    """Response model for updating project item field"""

    update_project_v2_item_field_value: Dict[str, Any] = Field(alias="updateProjectV2ItemFieldValue")


class DeleteProjectV2ItemResponse(BaseModel):
    """Response model for deleting project item"""

    delete_project_v2_item: Dict[str, Any] = Field(alias="deleteProjectV2Item")


class ArchiveProjectV2ItemResponse(BaseModel):
    """Response model for archiving project item"""

    archive_project_v2_item: Dict[str, Any] = Field(alias="archiveProjectV2Item")


class CreateProjectV2Response(BaseModel):
    """Response model for creating project"""

    create_project_v2: Dict[str, Any] = Field(alias="createProjectV2")


class UpdateProjectV2Response(BaseModel):
    """Response model for updating project"""

    update_project_v2: Dict[str, Any] = Field(alias="updateProjectV2")


class DeleteProjectV2Response(BaseModel):
    """Response model for deleting project"""

    delete_project_v2: Dict[str, Any] = Field(alias="deleteProjectV2")


class GitHubAPIError(Exception):
    """Exception for GitHub API errors"""

    def __init__(self, message: str, status_code: Optional[int] = None, errors: Optional[List[Dict[str, Any]]] = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)


class RateLimitError(GitHubAPIError):
    """Exception for rate limit errors"""

    def __init__(self, reset_time: Optional[int] = None):
        self.reset_time = reset_time
        super().__init__("Rate limit exceeded")
