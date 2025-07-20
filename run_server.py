#!/usr/bin/env python
"""
Wrapper script to run the GitHub Projects MCP Server
This handles the module import issues when running from Claude Code
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import and run the server
if __name__ == "__main__":
    from github_projects_mcp.server import main
    import asyncio
    asyncio.run(main())