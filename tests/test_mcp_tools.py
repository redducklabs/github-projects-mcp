"""Test MCP tools end-to-end via server"""

import pytest
import asyncio
import subprocess
import os
import json
from typing import Dict, Any

from mcp.client.stdio import stdio_client


class TestMCPTools:
    """Test MCP tools through the actual server"""

    @pytest.fixture
    async def mcp_server_client(self, test_config: Dict[str, Any]):
        """Fixture that provides an MCP client connected to our server"""
        # Set environment variables for the server
        env = os.environ.copy()
        env.update({
            "GITHUB_TOKEN": test_config["test_github_token"],
            "MCP_TRANSPORT": "stdio",
            "LOG_LEVEL": "ERROR"
        })
        
        # Start server process
        process = subprocess.Popen(
            ["python", "-m", "github_projects_mcp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=0
        )
        
        try:
            # Give server time to start
            await asyncio.sleep(1)
            
            # Create client
            async with stdio_client(process.stdin, process.stdout) as client:
                yield client
                
        finally:
            # Clean up process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    @pytest.mark.asyncio
    async def test_get_organization_projects_tool(self, mcp_server_client, test_config: Dict[str, Any]):
        """Test get_organization_projects MCP tool"""
        org_name = test_config["test_org_name"]
        
        try:
            result = await mcp_server_client.call_tool(
                "get_organization_projects",
                {"org_login": org_name, "first": 5}
            )
            
            assert result is not None
            # Result should be a list of projects
            projects = result.content[0].text if result.content else "[]"
            projects_data = json.loads(projects) if isinstance(projects, str) else projects
            
            assert isinstance(projects_data, list)
            
        except Exception as e:
            if "insufficient permissions" in str(e).lower():
                pytest.skip("Insufficient GitHub permissions")
            else:
                raise

    @pytest.mark.asyncio
    async def test_get_project_tool(self, mcp_server_client, test_config: Dict[str, Any]):
        """Test get_project MCP tool"""
        project_id = test_config["test_project_id"]
        
        try:
            result = await mcp_server_client.call_tool(
                "get_project",
                {"project_id": project_id}
            )
            
            assert result is not None
            project_data = result.content[0].text if result.content else "{}"
            project = json.loads(project_data) if isinstance(project_data, str) else project_data
            
            assert isinstance(project, dict)
            assert project.get("id") == project_id
            
        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip("Test project not found")
            else:
                raise

    @pytest.mark.asyncio
    async def test_get_project_items_tool(self, mcp_server_client, test_config: Dict[str, Any]):
        """Test get_project_items MCP tool"""
        project_id = test_config["test_project_id"]
        
        try:
            result = await mcp_server_client.call_tool(
                "get_project_items",
                {"project_id": project_id, "first": 10}
            )
            
            assert result is not None
            items_data = result.content[0].text if result.content else "[]"
            items = json.loads(items_data) if isinstance(items_data, str) else items_data
            
            assert isinstance(items, list)
            
        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip("Test project not found")
            else:
                raise

    @pytest.mark.asyncio
    async def test_get_project_fields_tool(self, mcp_server_client, test_config: Dict[str, Any]):
        """Test get_project_fields MCP tool"""
        project_id = test_config["test_project_id"]
        
        try:
            result = await mcp_server_client.call_tool(
                "get_project_fields",
                {"project_id": project_id}
            )
            
            assert result is not None
            fields_data = result.content[0].text if result.content else "[]"
            fields = json.loads(fields_data) if isinstance(fields_data, str) else fields_data
            
            assert isinstance(fields, list)
            
        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip("Test project not found")
            else:
                raise

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, mcp_server_client):
        """Test tool error handling with invalid inputs"""
        # Test with invalid project ID
        invalid_project_id = "PVT_invalid_id"
        
        with pytest.raises(Exception) as exc_info:
            await mcp_server_client.call_tool(
                "get_project",
                {"project_id": invalid_project_id}
            )
        
        # Should contain GitHub API error information
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["api error", "not found", "github"])

    @pytest.mark.asyncio
    async def test_all_tools_listed(self, mcp_server_client):
        """Test that all expected tools are available"""
        tools = await mcp_server_client.list_tools()
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "get_organization_projects",
            "get_user_projects", 
            "get_project",
            "get_project_items",
            "get_project_fields",
            "add_item_to_project",
            "update_item_field_value",
            "remove_item_from_project",
            "archive_item",
            "create_project",
            "update_project",
            "delete_project"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool {expected_tool} not found"

    @pytest.mark.asyncio
    async def test_tool_schemas(self, mcp_server_client):
        """Test that tools have proper parameter schemas"""
        tools = await mcp_server_client.list_tools()
        
        # Check specific tool schemas
        for tool in tools:
            if tool.name == "get_organization_projects":
                # Should have org_login parameter
                assert "org_login" in str(tool.inputSchema)
                assert "first" in str(tool.inputSchema)
            elif tool.name == "add_item_to_project":
                # Should have project_id and content_id parameters
                assert "project_id" in str(tool.inputSchema)
                assert "content_id" in str(tool.inputSchema)