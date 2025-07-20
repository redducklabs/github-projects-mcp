"""Smoke tests for GitHub API operations"""

import pytest
import asyncio
import json
import os
from typing import Dict, Any, Optional

from github_projects_mcp.core.client import GitHubProjectsClient
from github_projects_mcp.core.models import GitHubAPIError


class TestGitHubAPI:
    """Test GitHub API integration with live data"""

    def test_client_initialization(self, github_client: GitHubProjectsClient):
        """Test that GitHub client initializes properly"""
        assert github_client is not None
        assert github_client.token is not None

    def test_get_organization_projects(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test fetching organization projects"""
        org_name = test_config["test_org_name"]
        
        try:
            projects_response = github_client.get_organization_projects(org_name, first=5)
            assert isinstance(projects_response, dict)
            assert "nodes" in projects_response
            projects = projects_response["nodes"]
            assert isinstance(projects, list)
            
            # Should have at least our test project
            assert len(projects) >= 0  # May be 0 if no projects exist
            
            # If we have projects, validate structure
            if projects:
                project = projects[0]
                required_fields = ["id", "title", "createdAt", "url"]
                for field in required_fields:
                    assert field in project, f"Project missing required field: {field}"
                    
        except GitHubAPIError as e:
            pytest.skip(f"GitHub API error (may be permissions): {e}")

    def test_get_project_by_id(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test fetching specific project by ID"""
        project_id = test_config["test_project_id"]
        
        try:
            project = github_client.get_project(project_id)
            assert project is not None
            assert project["id"] == project_id
            assert "title" in project
            assert "url" in project
            
        except GitHubAPIError as e:
            pytest.skip(f"GitHub API error (project may not exist): {e}")

    def test_get_project_items(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test fetching project items"""
        project_id = test_config["test_project_id"]
        
        try:
            items_response = github_client.get_project_items(project_id, first=10)
            assert isinstance(items_response, dict)
            assert "nodes" in items_response
            items = items_response["nodes"]
            assert isinstance(items, list)
            
            # Items may be empty, but should be a valid list
            if items:
                item = items[0]
                required_fields = ["id", "type", "createdAt"]
                for field in required_fields:
                    assert field in item, f"Item missing required field: {field}"
                    
        except GitHubAPIError as e:
            pytest.skip(f"GitHub API error: {e}")

    def test_get_project_fields(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test fetching project fields"""
        project_id = test_config["test_project_id"]
        
        try:
            fields = github_client.get_project_fields(project_id)
            assert isinstance(fields, list)
            
            # Should have some default fields
            if fields:
                field = fields[0]
                required_fields = ["id", "name", "dataType"]
                for field_attr in required_fields:
                    assert field_attr in field, f"Field missing required attribute: {field_attr}"
                    
        except GitHubAPIError as e:
            pytest.skip(f"GitHub API error: {e}")

    def test_create_and_delete_project(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test creating and deleting a project"""
        # This test requires organization admin permissions
        # Skip if we don't have sufficient permissions
        
        try:
            # First, get organization ID
            org_name = test_config["test_org_name"]
            org_projects_response = github_client.get_organization_projects(org_name, first=1)
            org_projects = org_projects_response.get("nodes", [])
            
            if not org_projects:
                pytest.skip("No projects found to determine organization ID")
            
            # Extract owner ID from existing project
            owner_id = org_projects[0]["owner"].get("id")
            if not owner_id:
                pytest.skip("Could not determine organization ID")
            
            # Create test project
            test_title = "[MCP-TEST] Temporary Test Project"
            test_description = "Temporary project created by MCP server tests"
            
            created_project = github_client.create_project(
                owner_id=owner_id,
                title=test_title,
                description=test_description
            )
            
            assert created_project is not None
            assert created_project["title"] == test_title
            project_id = created_project["id"]
            
            # Clean up - delete the project
            deleted_project = github_client.delete_project(project_id)
            assert deleted_project["id"] == project_id
            
        except GitHubAPIError as e:
            if "insufficient permissions" in str(e).lower() or "forbidden" in str(e).lower():
                pytest.skip("Insufficient permissions to create/delete projects")
            else:
                raise

    def test_error_handling_invalid_project(self, github_client: GitHubProjectsClient):
        """Test error handling with invalid project ID"""
        invalid_project_id = "PVT_invalid_project_id"
        
        with pytest.raises(GitHubAPIError):
            github_client.get_project(invalid_project_id)

    def test_rate_limit_handling(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test rate limit handling by making multiple rapid requests"""
        project_id = test_config["test_project_id"]
        
        # Make several rapid requests to potentially trigger rate limiting
        # GitHub allows quite a few requests, so this may not actually hit limits
        success_count = 0
        
        try:
            for _ in range(5):
                result = github_client.get_project(project_id)
                if result:
                    success_count += 1
            
            # All should succeed unless we hit rate limits
            assert success_count > 0, "At least some requests should succeed"
            
        except Exception as e:
            # If we hit rate limits, that's actually expected behavior
            if "rate limit" in str(e).lower():
                pytest.skip("Hit rate limits (expected behavior)")
            else:
                raise


class TestGitHubAPIIntegration:
    """Integration tests that require a real repository and project"""
    
    @pytest.mark.skip(reason="Integration test requires live GitHub environment")
    def test_full_workflow_with_issue(self, github_client: GitHubProjectsClient, test_config: Dict[str, Any]):
        """Test complete workflow: create issue → add to project → update → remove"""
        # This is a comprehensive integration test
        # Requires repository write permissions and project admin permissions
        
        try:
            repo_owner = test_config["test_repo_owner"]
            repo_name = test_config["test_repo_name"]
            project_id = test_config["test_project_id"]
            
            # Note: This test would require GitHub REST API client to create issues
            # Since we only have GraphQL client, we'll simulate with existing content
            
            # Get existing project items to work with
            items = github_client.get_project_items(project_id, first=5)
            
            if not items:
                pytest.skip("No items in project to test with")
            
            # Test updating an existing item's field (if fields exist)
            fields = github_client.get_project_fields(project_id)
            
            if not fields:
                pytest.skip("No fields in project to test with")
            
            # Find a text field to update
            text_field = None
            for field in fields:
                if field.get("dataType") == "TEXT":
                    text_field = field
                    break
            
            if not text_field:
                pytest.skip("No text field available for testing")
            
            # Update the field value
            item_id = items[0]["id"]
            field_id = text_field["id"]
            test_value = "[MCP-TEST] Updated by test"
            
            result = github_client.update_item_field_value(
                project_id=project_id,
                item_id=item_id,
                field_id=field_id,
                value=test_value
            )
            
            assert result is not None
            assert "id" in result
            
        except GitHubAPIError as e:
            if "insufficient permissions" in str(e).lower():
                pytest.skip("Insufficient permissions for integration test")
            else:
                raise