#!/usr/bin/env python3
"""Verification script to check that the GitHub Projects MCP Server is properly set up"""

import sys
import os
from typing import List, Tuple

def check_import(module_name: str, description: str) -> Tuple[bool, str]:
    """Check if a module can be imported"""
    try:
        if module_name in ["github_projects_mcp.server", "github_projects_mcp.config"]:
            # Need to set dummy token for server/config import
            os.environ.setdefault("GITHUB_TOKEN", "dummy_for_verification")
        
        __import__(module_name)
        return True, f"[OK] {description}"
    except ImportError as e:
        return False, f"[FAIL] {description}: {e}"
    except Exception as e:
        # For config module, missing env var is expected in verification
        if module_name == "github_projects_mcp.config" and "GITHUB_TOKEN" in str(e):
            return True, f"[OK] {description} (env var check works)"
        return False, f"[WARN] {description}: {e}"

def check_dependencies() -> List[Tuple[bool, str]]:
    """Check all critical dependencies"""
    checks = [
        ("mcp.server.fastmcp", "MCP FastMCP SDK"),
        ("gql", "GraphQL client library"),
        ("gql.transport.requests", "GQL requests transport"),
        ("pydantic", "Pydantic for data validation"),
        ("requests", "HTTP requests library"),
        ("github_projects_mcp.core.client", "GitHub Projects client"),
        ("github_projects_mcp.core.models", "Pydantic models"),
        ("github_projects_mcp.config", "Configuration module"),
        ("github_projects_mcp.server", "MCP Server module"),
    ]
    
    results = []
    for module, description in checks:
        success, message = check_import(module, description)
        results.append((success, message))
    
    return results

def check_tool_creation() -> Tuple[bool, str]:
    """Check that MCP tools can be created"""
    try:
        from mcp.server.fastmcp import FastMCP
        
        mcp = FastMCP("Test Server")
        
        @mcp.tool()
        def test_tool(param: str) -> str:
            return f"Test: {param}"
        
        return True, "[OK] MCP tool creation works"
    except Exception as e:
        return False, f"[FAIL] MCP tool creation failed: {e}"

def main():
    """Main verification function"""
    print("GitHub Projects MCP Server Setup Verification")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"[OK] Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"[FAIL] Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)")
        return False
    
    print("\nChecking Dependencies:")
    print("-" * 30)
    
    # Check dependencies
    all_passed = True
    dependency_results = check_dependencies()
    for success, message in dependency_results:
        print(message)
        if not success:
            all_passed = False
    
    print("\nChecking Functionality:")
    print("-" * 30)
    
    # Check tool creation
    success, message = check_tool_creation()
    print(message)
    if not success:
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("All checks passed! Your GitHub Projects MCP Server is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.template to .env.test")
        print("2. Fill in your GitHub token and test project details")
        print("3. Run tests: pytest tests/")
        print("4. Start server: python -m github_projects_mcp.server")
        return True
    else:
        print("Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)