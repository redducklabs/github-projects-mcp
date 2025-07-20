"""Simple canary test for updating the public project issue"""

import pytest
import asyncio
import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from dotenv import load_dotenv


@pytest.mark.asyncio
async def test_update_canary():
    """Simple test that updates the canary issue in the public project"""
    
    # Load configuration
    load_dotenv(".env.test")
    
    config = {
        'github_token': os.getenv('TEST_GITHUB_TOKEN'),
        'org_name': os.getenv('TEST_ORG_NAME'),
        'project_id': os.getenv('TEST_PROJECT_ID'),
        'repo_owner': os.getenv('TEST_REPO_OWNER'),
        'repo_name': os.getenv('TEST_REPO_NAME'),
    }
    
    if not all(config.values()):
        pytest.skip("Missing required configuration")
    
    # Set up environment for MCP server
    os.environ['GITHUB_TOKEN'] = config['github_token']
    os.environ['LOG_LEVEL'] = 'ERROR'
    
    test_stats = {
        'total_tests': 0,
        'passed_tests': 0,
        'verified_tools': [],
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
    }
    
    try:
        from github_projects_mcp.server import mcp
        
        # Test 1: Get project
        test_stats['total_tests'] += 1
        result = await mcp.call_tool('get_project', {'project_id': config['project_id']})
        project = result[1]['result']
        test_stats['project_title'] = project.get('title', 'Unknown')
        test_stats['passed_tests'] += 1
        test_stats['verified_tools'].append('get_project')
        
        # Test 2: Get project items
        test_stats['total_tests'] += 1
        result = await mcp.call_tool('get_project_items', {'project_id': config['project_id'], 'first': 20})
        items = result[1]['result']
        test_stats['project_items_count'] = len(items)
        test_stats['passed_tests'] += 1
        test_stats['verified_tools'].append('get_project_items')
        
        # Test 3: Get organization projects
        test_stats['total_tests'] += 1
        result = await mcp.call_tool('get_organization_projects', {'org_login': config['org_name'], 'first': 10})
        projects = result[1]['result']
        test_stats['org_projects_count'] = len(projects)
        test_stats['passed_tests'] += 1
        test_stats['verified_tools'].append('get_organization_projects')
        
        # Calculate success rate
        test_stats['success_rate'] = (test_stats['passed_tests'] / test_stats['total_tests']) * 100
        
        # Update the canary issue
        update_canary_issue(config, test_stats)
        
        # Assert success
        assert test_stats['passed_tests'] == test_stats['total_tests'], f"Some tests failed: {test_stats}"
        
        print(f"[SUCCESS] Canary test passed! {test_stats['passed_tests']}/{test_stats['total_tests']} tests successful")
        
    except Exception as e:
        # Update issue with failure info
        test_stats['success_rate'] = (test_stats['passed_tests'] / max(test_stats['total_tests'], 1)) * 100
        test_stats['error'] = str(e)
        try:
            update_canary_issue(config, test_stats)
        except:
            pass
        raise


def update_canary_issue(config: Dict[str, Any], test_stats: Dict[str, Any]):
    """Update the canary issue with current test results"""
    headers = {
        'Authorization': f'token {config["github_token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Find the test issue
    issues_url = f'https://api.github.com/repos/{config["repo_owner"]}/{config["repo_name"]}/issues'
    response = requests.get(issues_url, headers=headers)
    response.raise_for_status()
    
    test_issue = None
    for issue in response.json():
        if '[MCP-TEST]' in issue['title'] and issue['state'] == 'open':
            test_issue = issue
            break
    
    if not test_issue:
        return  # No test issue to update
    
    # Generate updated content
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    success_icon = "✅" if test_stats.get('success_rate', 0) == 100 else "⚠️"
    
    body = f"""# 🤖 Automated Test Results

**Last Updated:** {timestamp}  
**Status:** {success_icon} {'PASSING' if test_stats.get('success_rate', 0) == 100 else 'FAILING'}

## Test Statistics
- **Total Tests Run:** {test_stats.get('total_tests', 0)}
- **Tests Passed:** {test_stats.get('passed_tests', 0)}
- **Tests Failed:** {test_stats.get('total_tests', 0) - test_stats.get('passed_tests', 0)}
- **Test Success Rate:** {test_stats.get('success_rate', 0):.1f}%

## API Operations Tested
- ✅ Organization Projects: {test_stats.get('org_projects_count', 0)} projects found
- ✅ Project Access: "{test_stats.get('project_title', 'Unknown')}"
- ✅ Project Items: {test_stats.get('project_items_count', 0)} items

## MCP Tools Verified
{chr(10).join('- ✅ `' + tool + '`' for tool in test_stats.get('verified_tools', []))}

## System Information
- **Python Version:** {test_stats.get('python_version', 'Unknown')}
- **Test Environment:** {config['repo_owner']}/{config['repo_name']}
- **Project ID:** `{config['project_id']}`

{"## Error Information\n```\n" + str(test_stats['error']) + "\n```\n" if test_stats.get('error') else ''}

---
*This issue is automatically updated by the GitHub Projects MCP Server test suite to demonstrate functionality and serve as a health check.*

**GitHub Projects MCP Server:** A Model Context Protocol server that provides GitHub Projects management tools for AI assistants like Claude.

🔗 **Repository:** https://github.com/{config['repo_owner']}/{config['repo_name']}  
📋 **Public Project:** https://github.com/orgs/{config['org_name']}/projects/6

### Recent Test History
This canary is updated every time the test suite runs, providing a live demonstration of the MCP server's capabilities.
"""
    
    # Update the issue
    update_url = f'https://api.github.com/repos/{config["repo_owner"]}/{config["repo_name"]}/issues/{test_issue["number"]}'
    update_data = {'body': body}
    response = requests.patch(update_url, headers=headers, json=update_data)
    response.raise_for_status()
    
    print(f"[OK] Updated canary issue #{test_issue['number']}")