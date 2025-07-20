"""Live integration test that creates/updates a test issue in the project"""

import pytest
import asyncio
import os
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from github_projects_mcp.core.client import GitHubProjectsClient


class TestLiveIntegration:
    """Live integration tests that create evidence in the public project"""
    
    @pytest.fixture(scope="class")
    def test_config(self) -> Dict[str, Any]:
        """Load test configuration"""
        load_dotenv(".env.test")
        
        config = {
            'github_token': os.getenv('TEST_GITHUB_TOKEN'),
            'org_name': os.getenv('TEST_ORG_NAME'),
            'project_id': os.getenv('TEST_PROJECT_ID'),
            'repo_owner': os.getenv('TEST_REPO_OWNER'),
            'repo_name': os.getenv('TEST_REPO_NAME'),
        }
        
        # Validate all required config is present
        missing = [k for k, v in config.items() if not v]
        if missing:
            pytest.skip(f"Missing required config: {missing}")
        
        return config
    
    def create_or_update_test_issue(self, config: Dict[str, Any], test_stats: Dict[str, Any]) -> str:
        """Create or update the test issue with current statistics"""
        headers = {
            'Authorization': f'token {config["github_token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        repo_owner = config['repo_owner']
        repo_name = config['repo_name']
        
        # Look for existing test issue
        issues_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
        response = requests.get(issues_url, headers=headers)
        response.raise_for_status()
        
        issues = response.json()
        test_issue = None
        
        for issue in issues:
            if '[MCP-TEST]' in issue['title'] and issue['state'] == 'open':
                test_issue = issue
                break
        
        # Generate issue content
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        title = "[MCP-TEST] GitHub Projects MCP Server Test Results"
        # Build body in safe parts
        header = f"""# 🤖 Automated Test Results
        
**Last Updated:** {timestamp}

## Test Statistics
- **Total Tests Run:** {test_stats.get('total_tests', 0)}
- **Tests Passed:** {test_stats.get('passed_tests', 0)}
- **Tests Failed:** {test_stats.get('failed_tests', 0)}
- **Test Success Rate:** {test_stats.get('success_rate', 0):.1f}%"""
        
        api_section = f"""
## API Operations Tested
- ✅ Organization Projects: {test_stats.get('org_projects_count', 0)} projects found
- ✅ Project Access: {test_stats.get('project_title', 'Unknown')}
- ✅ Project Items: {test_stats.get('project_items_count', 0)} items
- ✅ Project Fields: {test_stats.get('project_fields_count', 0)} fields"""
        
        tools_list = test_stats.get('verified_tools', [])
        tools_text = '\n'.join('- ✅ `' + tool + '`' for tool in tools_list)
        tools_section = f"""
## MCP Tools Verified
{tools_text}"""
        
        system_section = f"""
## System Information
- **Python Version:** {test_stats.get('python_version', 'Unknown')}
- **MCP SDK Version:** {test_stats.get('mcp_version', 'Unknown')}
- **GraphQL Client:** {test_stats.get('gql_version', 'Unknown')}

## Test Environment
- **Repository:** {repo_owner}/{repo_name}
- **Project ID:** `{config['project_id']}`
- **Organization:** {config['org_name']}"""
        
        footer = f"""
---
*This issue is automatically updated by the GitHub Projects MCP Server test suite to demonstrate functionality and serve as a health check.*

**GitHub Projects MCP Server:** A Model Context Protocol server that provides GitHub Projects management tools for AI assistants like Claude.

🔗 **Repository:** https://github.com/{repo_owner}/{repo_name}
📋 **Public Project:** https://github.com/orgs/{config['org_name']}/projects/6"""
        
        body = header + api_section + tools_section + system_section + footer
        
        if test_issue:
            # Update existing issue
            update_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{test_issue["number"]}'
            update_data = {
                'title': title,
                'body': body
            }
            response = requests.patch(update_url, headers=headers, json=update_data)
            response.raise_for_status()
            print(f"Updated existing test issue #{test_issue['number']}")
            return test_issue['node_id']  # GitHub GraphQL node ID
        else:
            # Create new issue
            create_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
            create_data = {
                'title': title,
                'body': body,
                'labels': ['automated-test', 'mcp-server', 'documentation']
            }
            response = requests.post(create_url, headers=headers, json=create_data)
            response.raise_for_status()
            new_issue = response.json()
            print(f"Created new test issue #{new_issue['number']}")
            return new_issue['node_id']
    
    @pytest.mark.asyncio
    async def test_full_mcp_integration_with_evidence(self, test_config: Dict[str, Any]):
        """Complete integration test that creates evidence in the public project"""
        
        # Set up environment for MCP server
        os.environ['GITHUB_TOKEN'] = test_config['github_token']
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        test_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'verified_tools': [],
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        }
        
        try:
            # Import MCP server
            from github_projects_mcp.server import mcp
            
            # Test 1: List Accessible Projects (Discovery)
            test_stats['total_tests'] += 1
            try:
                result = await mcp.call_tool('list_accessible_projects', {
                    'first': 20
                })
                accessible_projects = result[1]['result']
                test_stats['accessible_projects_count'] = len(accessible_projects)
                test_stats['passed_tests'] += 1
                test_stats['verified_tools'].append('list_accessible_projects')
                print(f"✓ Found {len(accessible_projects)} accessible projects")
            except Exception as e:
                test_stats['failed_tests'] += 1
                test_stats['list_accessible_projects_error'] = str(e)
                print(f"✗ Failed to list accessible projects: {e}")
            
            # Test 2: Organization Projects
            test_stats['total_tests'] += 1
            try:
                result = await mcp.call_tool('get_organization_projects', {
                    'org_login': test_config['org_name'], 
                    'first': 10
                })
                projects = result[1]['result']
                test_stats['org_projects_count'] = len(projects)
                test_stats['passed_tests'] += 1
                test_stats['verified_tools'].append('get_organization_projects')
            except Exception as e:
                test_stats['failed_tests'] += 1
                pytest.fail(f"get_organization_projects failed: {e}")
            
            # Test 2: Specific Project
            test_stats['total_tests'] += 1
            try:
                result = await mcp.call_tool('get_project', {
                    'project_id': test_config['project_id']
                })
                project = result[1]['result']
                test_stats['project_title'] = project.get('title', 'Unknown')
                test_stats['passed_tests'] += 1
                test_stats['verified_tools'].append('get_project')
            except Exception as e:
                test_stats['failed_tests'] += 1
                pytest.fail(f"get_project failed: {e}")
            
            # Test 3: Project Items
            test_stats['total_tests'] += 1
            try:
                result = await mcp.call_tool('get_project_items', {
                    'project_id': test_config['project_id'],
                    'first': 20
                })
                items = result[1]['result']
                test_stats['project_items_count'] = len(items)
                test_stats['passed_tests'] += 1
                test_stats['verified_tools'].append('get_project_items')
            except Exception as e:
                test_stats['failed_tests'] += 1
                pytest.fail(f"get_project_items failed: {e}")
            
            # Test 4: Project Fields
            test_stats['total_tests'] += 1
            try:
                result = await mcp.call_tool('get_project_fields', {
                    'project_id': test_config['project_id']
                })
                fields = result[1]['result']
                test_stats['project_fields_count'] = len(fields)
                test_stats['passed_tests'] += 1
                test_stats['verified_tools'].append('get_project_fields')
            except Exception as e:
                test_stats['failed_tests'] += 1
                pytest.fail(f"get_project_fields failed: {e}")
            
            # Calculate success rate
            test_stats['success_rate'] = (test_stats['passed_tests'] / test_stats['total_tests']) * 100 if test_stats['total_tests'] > 0 else 0
            
            # Get package versions
            try:
                import mcp
                test_stats['mcp_version'] = getattr(mcp, '__version__', 'Unknown')
            except:
                test_stats['mcp_version'] = 'Unknown'
            
            try:
                import gql
                test_stats['gql_version'] = getattr(gql, '__version__', 'Unknown')
            except:
                test_stats['gql_version'] = 'Unknown'
            
            # Create or update test issue
            issue_node_id = self.create_or_update_test_issue(test_config, test_stats)
            
            # Test 5: Add issue to project (if we successfully created/updated an issue)
            if issue_node_id:
                test_stats['total_tests'] += 1
                try:
                    result = await mcp.call_tool('add_item_to_project', {
                        'project_id': test_config['project_id'],
                        'content_id': issue_node_id
                    })
                    test_stats['passed_tests'] += 1
                    test_stats['verified_tools'].append('add_item_to_project')
                    print("[OK] Test issue successfully added to project!")
                except Exception as e:
                    # This might fail if the issue is already in the project
                    if "already exists" in str(e).lower():
                        test_stats['passed_tests'] += 1
                        test_stats['verified_tools'].append('add_item_to_project')
                        print("[OK] Test issue already in project (expected)")
                    else:
                        test_stats['failed_tests'] += 1
                        print(f"[WARN] Could not add issue to project: {e}")
            
            # Recalculate final success rate
            test_stats['success_rate'] = (test_stats['passed_tests'] / test_stats['total_tests']) * 100 if test_stats['total_tests'] > 0 else 0
            
            # Assert overall success
            assert test_stats['passed_tests'] >= 4, f"Expected at least 4 passing tests, got {test_stats['passed_tests']}"
            assert test_stats['success_rate'] >= 80, f"Expected at least 80% success rate, got {test_stats['success_rate']:.1f}%"
            
            print(f"\n[SUCCESS] Integration test completed successfully!")
            print(f"[STATS] Results: {test_stats['passed_tests']}/{test_stats['total_tests']} tests passed ({test_stats['success_rate']:.1f}% success rate)")
            print(f"[TOOLS] Tools verified: {', '.join(test_stats['verified_tools'])}")
            
        except Exception as e:
            # Even if tests fail, try to update the issue with failure info
            test_stats['success_rate'] = (test_stats['passed_tests'] / max(test_stats['total_tests'], 1)) * 100
            try:
                self.create_or_update_test_issue(test_config, test_stats)
            except:
                pass  # Don't fail the test if we can't update the issue
            raise