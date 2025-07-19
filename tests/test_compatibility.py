"""Test compatibility with updated dependencies"""

import pytest
import os
import importlib.util
import subprocess
import sys
from unittest.mock import patch


class TestCompatibility:
    """Test that the application works with updated dependencies"""

    def test_server_module_imports(self):
        """Test that the server module imports successfully"""
        # Mock the environment variable to avoid config errors
        with patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            try:
                import github_projects_mcp.server
                assert True, "Server module imported successfully"
            except ImportError as e:
                pytest.fail(f"Server module failed to import: {e}")

    def test_core_client_imports(self):
        """Test that core client module imports successfully"""
        try:
            from github_projects_mcp.core.client import GitHubProjectsClient
            from github_projects_mcp.core.models import GitHubAPIError, RateLimitError
            assert True, "Core modules imported successfully"
        except ImportError as e:
            pytest.fail(f"Core modules failed to import: {e}")

    def test_mcp_fastmcp_import(self):
        """Test that FastMCP imports correctly with updated MCP SDK"""
        try:
            from mcp.server.fastmcp import FastMCP
            mcp = FastMCP("Test Server")
            assert mcp is not None
            assert hasattr(mcp, 'tool'), "FastMCP should have tool decorator"
        except ImportError as e:
            pytest.fail(f"FastMCP import failed: {e}")

    def test_gql_import(self):
        """Test that gql imports correctly with updated version"""
        try:
            from gql import Client, gql
            from gql.transport.requests import RequestsHTTPTransport
            assert True, "GQL modules imported successfully"
        except ImportError as e:
            pytest.fail(f"GQL modules failed to import: {e}")

    def test_pydantic_models(self):
        """Test that Pydantic models work with current version"""
        try:
            from github_projects_mcp.core.models import ProjectV2, GitHubAPIError
            
            # Test model creation
            project_data = {
                "id": "test_id",
                "title": "Test Project", 
                "public": True,
                "closed": False,
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:00Z",
                "number": 1,
                "url": "https://github.com/test",
                "owner": {"login": "test_owner"}
            }
            
            project = ProjectV2(**project_data)
            assert project.id == "test_id"
            assert project.title == "Test Project"
            
        except Exception as e:
            pytest.fail(f"Pydantic models failed: {e}")

    def test_server_with_dummy_config(self):
        """Test server startup with minimal configuration"""
        env = os.environ.copy()
        env.update({
            "GITHUB_TOKEN": "dummy_token_for_testing",
            "MCP_TRANSPORT": "stdio",
            "LOG_LEVEL": "ERROR"
        })
        
        # Test that server can start (but will fail quickly due to dummy token)
        process = subprocess.Popen(
            [sys.executable, "-m", "github_projects_mcp.server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Give it a moment to start up
            stdout, stderr = process.communicate(timeout=5)
            
            # Server should start but may fail due to dummy token
            # As long as it doesn't fail with import errors, we're good
            assert "ModuleNotFoundError" not in stderr
            assert "ImportError" not in stderr
            
        except subprocess.TimeoutExpired:
            # Server started successfully (didn't exit immediately)
            process.terminate()
            process.wait()
            assert True, "Server started successfully with updated dependencies"

    def test_tool_definitions(self):
        """Test that tool definitions are properly created"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            try:
                import github_projects_mcp.server as server_module
                
                # Check that mcp instance exists and has tools
                assert hasattr(server_module, 'mcp')
                mcp_instance = server_module.mcp
                assert mcp_instance is not None
                
            except Exception as e:
                pytest.fail(f"Tool definitions failed: {e}")

    def test_config_validation(self):
        """Test configuration validation with updated dependencies"""
        try:
            from github_projects_mcp.config import Config
            
            # Test with minimal valid config
            with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
                config = Config()
                assert config.github_token == "test_token"
                assert config.transport == "stdio"  # default
                
                # Test transport validation
                config.transport = "sse"
                config.validate_transport()  # Should not raise
                
                config.transport = "invalid"
                with pytest.raises(ValueError):
                    config.validate_transport()
                    
        except Exception as e:
            pytest.fail(f"Configuration validation failed: {e}")

    def test_all_imports_work_together(self):
        """Test that all major components can be imported together"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            try:
                # Import everything we need
                from mcp.server.fastmcp import FastMCP
                from gql import Client, gql
                from github_projects_mcp.core.client import GitHubProjectsClient
                from github_projects_mcp.core.models import ProjectV2, GitHubAPIError
                from github_projects_mcp.config import Config
                import github_projects_mcp.server
                
                # Basic functionality test
                mcp = FastMCP("Test")
                
                @mcp.tool()
                def test_tool(param: str) -> str:
                    return f"Test: {param}"
                
                assert True, "All components work together"
                
            except Exception as e:
                pytest.fail(f"Integration test failed: {e}")