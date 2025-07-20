"""Test MCP server transport modes"""

import asyncio
import json
import os
import subprocess
import time
import pytest
from typing import Dict, Any

# Import available MCP clients
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client


class TestMCPTransports:
    """Test all MCP transport modes"""

    @pytest.mark.asyncio
    async def test_stdio_transport(self, test_config: Dict[str, Any]):
        """Test stdio transport mode"""
        # Set environment variables for the server
        env = os.environ.copy()
        env.update({
            "GITHUB_TOKEN": test_config["test_github_token"],
            "MCP_TRANSPORT": "stdio",
            "LOG_LEVEL": "ERROR"  # Reduce noise in tests
        })
        
        # Create server parameters (use same Python executable as test)
        import sys
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "github_projects_mcp.server"],
            env=env
        )
        
        # Test with stdio client
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                
                # Test basic capability
                tools_result = await client.list_tools()
                tools = tools_result.tools
                assert len(tools) > 0
                
                # Look for our expected tools
                tool_names = [tool.name for tool in tools]
                expected_tools = [
                    "get_organization_projects",
                    "get_user_projects", 
                    "get_project",
                    "add_item_to_project"
                ]
                
                for expected_tool in expected_tools:
                    assert expected_tool in tool_names, f"Tool {expected_tool} not found"

    @pytest.mark.skip(reason="SSE transport requires special server configuration")
    async def test_sse_transport(self, test_config: Dict[str, Any]):
        """Test Server-Sent Events transport mode"""
        port = int(os.getenv("MCP_TEST_PORT_SSE", "8001"))
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            "GITHUB_TOKEN": test_config["test_github_token"],
            "MCP_TRANSPORT": "sse",
            "MCP_PORT": str(port),
            "LOG_LEVEL": "ERROR"
        })
        
        # Start server process
        process = subprocess.Popen(
            ["python", "-m", "github_projects_mcp.server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Give server time to start
            await asyncio.sleep(3)
            
            # Test connection to SSE endpoint
            url = f"http://localhost:{port}/sse"
            
            async with sse_client(url) as client:
                # Test basic capability
                tools = await client.list_tools()
                assert len(tools) > 0
                
                # Verify we have GitHub tools
                tool_names = [tool.name for tool in tools]
                assert "get_organization_projects" in tool_names
                
        except Exception as e:
            # Capture server logs for debugging
            stdout, stderr = process.communicate(timeout=1)
            pytest.fail(f"SSE test failed: {e}\nServer stdout: {stdout}\nServer stderr: {stderr}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    @pytest.mark.skip(reason="HTTP transport requires special server configuration")
    async def test_http_transport(self, test_config: Dict[str, Any]):
        """Test HTTP streaming transport mode"""
        port = int(os.getenv("MCP_TEST_PORT_HTTP", "8002"))
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            "GITHUB_TOKEN": test_config["test_github_token"],
            "MCP_TRANSPORT": "http",
            "MCP_PORT": str(port),
            "LOG_LEVEL": "ERROR"
        })
        
        # Start server process
        process = subprocess.Popen(
            ["python", "-m", "github_projects_mcp.server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Give server time to start
            await asyncio.sleep(3)
            
            # Test connection to HTTP endpoint
            url = f"http://localhost:{port}"
            
            async with streamablehttp_client(url) as client:
                # Test basic capability
                tools = await client.list_tools()
                assert len(tools) > 0
                
                # Verify we have GitHub tools
                tool_names = [tool.name for tool in tools]
                assert "get_project" in tool_names
                
        except Exception as e:
            # Capture server logs for debugging
            stdout, stderr = process.communicate(timeout=1)
            pytest.fail(f"HTTP test failed: {e}\nServer stdout: {stdout}\nServer stderr: {stderr}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    @pytest.mark.skip(reason="Transport validation needs to be implemented in server")
    async def test_invalid_transport(self):
        """Test that invalid transport mode fails gracefully"""
        env = os.environ.copy()
        env.update({
            "GITHUB_TOKEN": "dummy_token", 
            "MCP_TRANSPORT": "invalid_transport"
        })
        
        process = subprocess.Popen(
            ["python", "-m", "github_projects_mcp.server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for process to exit
        stdout, stderr = process.communicate(timeout=10)
        
        # Should exit with error
        assert process.returncode != 0
        assert "invalid_transport" in stderr.lower() or "unsupported transport" in stderr.lower()