# GitHub Projects MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with GitHub Projects using GraphQL. This server exposes GitHub Projects functionality through standardized MCP tools that can be used by LLMs and other MCP clients.

## Features

- **Complete GitHub Projects API Coverage**: All major GitHub Projects operations including:
  - Get projects (organization/user level)
  - Manage project items (add, update, remove, archive)
  - Handle project fields and field values
  - Create, update, and delete projects
- **Multiple Transport Modes**: Supports stdio, Server-Sent Events (SSE), and HTTP streaming
- **Robust Error Handling**: Proper GitHub API error surfacing and configurable rate limit retries
- **Type Safety**: Built with Pydantic models for reliable data validation
- **Environment-based Configuration**: Flexible configuration through environment variables

## Installation

### From Source

```bash
git clone https://github.com/redducklabs/github-projects-mcp.git
cd github-projects-mcp
pip install -e .
```

### Using pip

```bash
pip install github-projects-mcp
```

### Using uv

```bash
uv add github-projects-mcp
```

## Configuration

The server is configured entirely through environment variables:

### Required Configuration

- `GITHUB_TOKEN`: GitHub Personal Access Token with appropriate permissions
  - Required scopes: `project`, `read:project`
  - For organization projects: additional repository/organization permissions may be needed

### Optional Configuration

- `API_MAX_RETRIES`: Maximum retries for rate-limited requests (default: `3`)
- `API_RETRY_DELAY`: Delay in seconds between retries (default: `60`)
- `MCP_TRANSPORT`: Transport mode - `stdio`, `sse`, or `http` (default: `stdio`)
- `MCP_HOST`: Host for SSE/HTTP modes (default: `localhost`)
- `MCP_PORT`: Port for SSE/HTTP modes (default: `8000`)
- `LOG_LEVEL`: Logging level - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

### Setting up GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with the following scopes:
   - `project` (for managing projects)
   - `read:project` (for reading project data)
3. Set the token as an environment variable:

```bash
export GITHUB_TOKEN="your_token_here"
```

## Usage

### Running the Server

#### Stdio Mode (Default)
```bash
# Using the installed script
github-projects-mcp

# Or using Python module
python -m github_projects_mcp.server

# Or using uv
uv run github_projects_mcp/server.py
```

#### Server-Sent Events Mode
```bash
export MCP_TRANSPORT=sse
export MCP_PORT=8000
github-projects-mcp
```

#### HTTP Streaming Mode
```bash
export MCP_TRANSPORT=http
export MCP_PORT=8000
github-projects-mcp
```

### Available Tools

The server exposes the following MCP tools:

#### Project Management
- `get_organization_projects(org_login, first=20)` - Get projects for an organization
- `get_user_projects(user_login, first=20)` - Get projects for a user  
- `get_project(project_id)` - Get a specific project by ID
- `create_project(owner_id, title, description=None)` - Create a new project
- `update_project(project_id, title=None, description=None, readme=None, public=None)` - Update project
- `delete_project(project_id)` - Delete a project

#### Project Items Management
- `get_project_items(project_id, first=50)` - Get items in a project
- `add_item_to_project(project_id, content_id)` - Add an item to project
- `update_item_field_value(project_id, item_id, field_id, value)` - Update item field
- `remove_item_from_project(project_id, item_id)` - Remove item from project
- `archive_item(project_id, item_id)` - Archive a project item

#### Project Fields
- `get_project_fields(project_id)` - Get fields in a project

## Using with Claude Code

The GitHub Projects MCP Server can be easily integrated with Claude Code to give Claude access to your GitHub Projects. Here's how to set it up:

### Quick Setup (from PyPI)

1. **Install the server:**
   ```bash
   pip install github-projects-mcp
   ```

2. **Add to Claude Code:**
   ```bash
   claude mcp add github-projects github-projects-mcp -e GITHUB_TOKEN=your_token_here
   ```

3. **Start using in Claude Code:**
   - Type `@github-projects` to reference the server
   - Use tools like "get organization projects" or "add item to project"

### Setup from Source

For development or if you want to run the latest version from source:

1. **Create and set up virtual environment (Recommended):**
   ```bash
   git clone https://github.com/redducklabs/github-projects-mcp.git
   cd github-projects-mcp
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   ./venv/Scripts/activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies and package:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Install package in development mode
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   python verify_setup.py
   ```

4. **Add to Claude Code (Recommended approach):**
   ```bash
   # Using virtual environment Python with direct script path
   claude mcp add github-projects ./venv/Scripts/python github_projects_mcp/server.py -e GITHUB_TOKEN=your_token_here -e PYTHONPATH=/full/path/to/github-projects-mcp
   
   # On macOS/Linux, use:
   # claude mcp add github-projects ./venv/bin/python github_projects_mcp/server.py -e GITHUB_TOKEN=your_token_here -e PYTHONPATH=/full/path/to/github-projects-mcp
   ```

5. **Alternative approaches:**
   ```bash
   # Option A: System Python with script path (if no virtual env)
   claude mcp add github-projects python github_projects_mcp/server.py -e GITHUB_TOKEN=your_token_here -e PYTHONPATH=/full/path/to/github-projects-mcp
   
   # Option B: Module approach (Note: claude mcp doesn't support -m flag)
   # This won't work: claude mcp add github-projects python -m github_projects_mcp.server
   ```

6. **Manual JSON configuration:**
   ```json
   {
     "mcpServers": {
       "github-projects": {
         "command": "./venv/Scripts/python",
         "args": ["github_projects_mcp/server.py"],
         "env": {
           "GITHUB_TOKEN": "your_github_token_here",
           "PYTHONPATH": "/full/path/to/github-projects-mcp"
         }
       }
     }
   }
   ```

7. **For development with hot reload:**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Add to Claude Code with debug logging
   claude mcp add github-projects-dev ./venv/Scripts/python github_projects_mcp/server.py -e GITHUB_TOKEN=your_token -e LOG_LEVEL=DEBUG -e PYTHONPATH=/full/path/to/github-projects-mcp
   ```

### Important Notes for Source Installation:

- **Virtual Environment**: Highly recommended to avoid dependency conflicts
- **PYTHONPATH**: Required when using direct script path to ensure module imports work
- **Claude MCP Limitations**: The `python -m module` syntax is not supported by `claude mcp add`
- **Path Requirements**: Use relative paths like `./venv/Scripts/python` for portability
- **Dependencies**: Must install both runtime (`requirements.txt`) and the package itself (`pip install -e .`)

### Manual Configuration

If you prefer to configure manually, add this to your Claude Code MCP configuration:

**Local/Project Configuration:**
```bash
# Add to local project
claude mcp add github-projects github-projects-mcp -e GITHUB_TOKEN=your_token_here --scope local

# Add to shared project configuration  
claude mcp add github-projects github-projects-mcp -e GITHUB_TOKEN=your_token_here --scope project
```

**Advanced Configuration:**
```json
{
  "mcpServers": {
    "github-projects": {
      "command": "github-projects-mcp",
      "args": [],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "API_MAX_RETRIES": "3",
        "API_RETRY_DELAY": "60",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Using Different Transport Modes:**

For stdio (default):
```bash
claude mcp add github-projects github-projects-mcp -e GITHUB_TOKEN=your_token -e MCP_TRANSPORT=stdio
```

For SSE server:
```bash
claude mcp add github-projects-sse github-projects-mcp -e GITHUB_TOKEN=your_token -e MCP_TRANSPORT=sse -e MCP_PORT=8001
```

For HTTP server:
```bash
claude mcp add github-projects-http github-projects-mcp -e GITHUB_TOKEN=your_token -e MCP_TRANSPORT=http -e MCP_PORT=8002
```

### Usage in Claude Code

Once configured, you can use the GitHub Projects server in Claude Code conversations:

**Reference the server:**
```
@github-projects help me manage my project
```

**Example conversations:**
```
"@github-projects show me all projects for my organization 'mycompany'"

"@github-projects add issue #123 from repo mycompany/myproject to project PVT_kwDOABCDEF"

"@github-projects update the status field for item PVTI_lADOGHIJKL to 'In Progress'"

"@github-projects create a new project called 'Q1 Planning' for organization mycompany"
```

**Check server status:**
In Claude Code, you can check if the server is working:
```
/mcp
```

### Security Notes

- **Token Security**: Your GitHub token is stored securely in Claude Code's configuration
- **Permissions**: The server only needs `project` and `read:project` scopes
- **Local Access**: All communication with GitHub happens through your local server

### Troubleshooting

**Server not appearing:**
```bash
# Check MCP server status
/mcp

# Restart Claude Code after adding the server
```

**GitHub Token Issues:**
- **Classic vs Fine-grained tokens**: For organization projects, you need a **Fine-grained Personal Access Token** (not Classic)
- **Required scopes**: `Projects: Read/Write` (for fine-grained) or `project` + `read:project` (for classic)
- **Organization access**: Ensure the token has access to your organization
- **Generate fine-grained token**: Go to https://github.com/settings/tokens?type=beta

**Source Installation Issues:**
```bash
# ModuleNotFoundError when starting server
# Solution: Use virtual environment and install dependencies
python -m venv venv
./venv/Scripts/activate  # Windows
pip install -r requirements.txt
pip install -e .

# Server fails with import errors
# Solution: Add PYTHONPATH environment variable
claude mcp add github-projects ./venv/Scripts/python github_projects_mcp/server.py -e GITHUB_TOKEN=token -e PYTHONPATH=/full/path/to/project

# Claude MCP add fails with "-m" option
# This won't work: claude mcp add server python -m module.server
# Use direct script path instead: claude mcp add server python module/server.py
```

**Permission errors:**
- For organization projects, use **Fine-grained Personal Access Token** with organization resource access
- Ensure you're a member of the organization with appropriate project permissions

**Connection issues:**
- Check your internet connection
- Verify the GitHub token is valid and not expired  
- Test token with: `gh auth status` or `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`
- For Windows: Unicode console issues may appear but don't affect functionality

## Using with VS Code

VS Code supports MCP servers through GitHub Copilot (requires VS Code 1.102+ with MCP support enabled):

### Option 1: Using MCP Commands (Recommended)

1. **Install the MCP server:**
   ```bash
   pip install github-projects-mcp
   ```

2. **Add server using VS Code command:**
   - Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Run `MCP: Add Server`
   - Choose workspace or global configuration
   - Enter server details when prompted

### Option 2: Manual Configuration

1. **Install the server:**
   ```bash
   pip install github-projects-mcp
   ```

2. **Create MCP configuration file:**

   **For workspace-specific:** `.vscode/mcp.json`
   
   **For user-wide:** Use Command Palette → `MCP: Open User Configuration`

   ```json
   {
     "inputs": [
       {
         "type": "promptString",
         "id": "github-token",
         "description": "GitHub Personal Access Token",
         "password": true
       }
     ],
     "servers": {
       "github-projects": {
         "type": "stdio",
         "command": "github-projects-mcp",
         "env": {
           "GITHUB_TOKEN": "${input:github-token}"
         }
       }
     }
   }
   ```

3. **Restart VS Code** and configure your GitHub token when prompted

## Using with Claude Desktop

### Option 1: Install via DXT Extension (Recommended)

When available, download the `.dxt` file from the [releases page](https://github.com/redducklabs/github-projects-mcp/releases) and install:

1. **Download the `.dxt` file** from the latest release
2. **Open Claude Desktop**
3. **Install extension** by dragging the `.dxt` file into Claude Desktop or using the extension installer
4. **Configure your GitHub token** when prompted

### Option 2: Manual Installation

1. **Install the MCP server:**
   ```bash
   pip install github-projects-mcp
   ```

2. **Add to Claude Desktop configuration:**

   **On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   
   **On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "github-projects": {
         "command": "github-projects-mcp",
         "env": {
           "GITHUB_TOKEN": "your_github_token_here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

### Getting Your GitHub Token

For both VS Code and Claude Desktop setup:

1. **Go to GitHub Settings** → Developer settings → Personal access tokens
2. **Create a new token** with these scopes:
   - `project` (for managing projects)
   - `read:project` (for reading project data)
3. **Copy the token** and use it in your configuration

**For organization projects:** Use a Fine-grained Personal Access Token with organization access.

### Example Usage with MCP Client

For developers integrating programmatically:

```python
# Example: Get organization projects
projects = await mcp_client.call_tool("get_organization_projects", {
    "org_login": "myorg",
    "first": 10
})

# Example: Add issue to project
result = await mcp_client.call_tool("add_item_to_project", {
    "project_id": "PVT_kwDOABCDEF",
    "content_id": "I_kwDOGHIJKL"
})

# Example: Update project item field
await mcp_client.call_tool("update_item_field_value", {
    "project_id": "PVT_kwDOABCDEF", 
    "item_id": "PVTI_lADOGHIJKL",
    "field_id": "PVTF_lADOGHIJKL", 
    "value": "In Progress"
})
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/redducklabs/github-projects-mcp.git
cd github-projects-mcp
pip install -e .
pip install -r requirements-dev.txt
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy github_projects_mcp/
```

## Architecture

- **`github_projects_mcp/core/client.py`**: GraphQL client wrapper with retry logic
- **`github_projects_mcp/core/models.py`**: Pydantic models for type safety
- **`github_projects_mcp/config.py`**: Environment-based configuration management  
- **`github_projects_mcp/server.py`**: FastMCP server with tool definitions

## Error Handling

- **GitHub API Errors**: All GitHub API errors are surfaced to the MCP client with detailed error messages
- **Rate Limiting**: Automatic retry with configurable delays for rate limit errors
- **Validation**: Pydantic models ensure data integrity and provide clear validation errors
- **Configuration**: Server fails fast on startup if required configuration is missing

## Security Considerations

- **Token Security**: GitHub tokens are loaded from environment variables only
- **Scope Limitation**: Requires minimal necessary scopes (`project`, `read:project`)
- **Error Information**: API errors are sanitized before being passed to clients

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite and linting
5. Submit a pull request

## License

GNU General Public License v3.0 - see LICENSE file for details.

## Troubleshooting

### Common Issues

**Server fails to start with "Required environment variable GITHUB_TOKEN is not set"**
- Set the `GITHUB_TOKEN` environment variable with a valid GitHub PAT

**GitHub API errors about insufficient permissions**
- Ensure your GitHub token has `project` and `read:project` scopes
- For organization projects, you may need additional repository permissions

**Rate limit errors**
- The server automatically retries rate-limited requests
- Increase `API_RETRY_DELAY` for longer waits between retries
- Reduce request frequency or use a token with higher rate limits

**Transport mode errors**
- Ensure `MCP_TRANSPORT` is set to `stdio`, `sse`, or `http`
- For SSE/HTTP modes, ensure the specified port is available

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
github-projects-mcp
```
