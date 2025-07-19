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

- `GITHUB_API_MAX_RETRIES`: Maximum retries for rate-limited requests (default: `3`)
- `GITHUB_API_RETRY_DELAY`: Delay in seconds between retries (default: `60`)
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

1. **Clone and install from source:**
   ```bash
   git clone https://github.com/redducklabs/github-projects-mcp.git
   cd github-projects-mcp
   pip install -e .
   ```

2. **Verify installation:**
   ```bash
   python verify_setup.py
   ```

3. **Add to Claude Code using full Python path:**
   ```bash
   # Option 1: Use the installed module
   claude mcp add github-projects python -m github_projects_mcp.server -e GITHUB_TOKEN=your_token_here
   
   # Option 2: Use direct script path (replace with your actual path)
   claude mcp add github-projects python /path/to/github-projects-mcp/github_projects_mcp/server.py -e GITHUB_TOKEN=your_token_here
   ```

4. **Alternative: Configure with absolute path in JSON:**
   ```json
   {
     "mcpServers": {
       "github-projects": {
         "command": "python",
         "args": ["/full/path/to/github-projects-mcp/github_projects_mcp/server.py"],
         "env": {
           "GITHUB_TOKEN": "your_github_token_here",
           "PYTHONPATH": "/full/path/to/github-projects-mcp"
         }
       }
     }
   }
   ```

5. **For development with hot reload:**
   ```bash
   # Set up development environment
   pip install -e .
   pip install -r requirements-dev.txt
   
   # Add to Claude Code with development settings
   claude mcp add github-projects-dev python -m github_projects_mcp.server -e GITHUB_TOKEN=your_token -e LOG_LEVEL=DEBUG
   ```

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
        "GITHUB_API_MAX_RETRIES": "3",
        "GITHUB_API_RETRY_DELAY": "60",
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

**Permission errors:**
- Ensure your GitHub token has `project` and `read:project` scopes
- For organization projects, you may need additional repository permissions

**Connection issues:**
- Check your internet connection
- Verify the GitHub token is valid and not expired
- Try different transport modes if stdio isn't working

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

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

**Server fails to start with "Required environment variable GITHUB_TOKEN is not set"**
- Set the `GITHUB_TOKEN` environment variable with a valid GitHub PAT

**GitHub API errors about insufficient permissions**
- Ensure your GitHub token has `project` and `read:project` scopes
- For organization projects, you may need additional repository permissions

**Rate limit errors**
- The server automatically retries rate-limited requests
- Increase `GITHUB_API_RETRY_DELAY` for longer waits between retries
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
