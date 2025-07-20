#!/usr/bin/env python3
"""Debug script to test the list_accessible_projects functionality"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment
load_dotenv()

from github_projects_mcp.core.client import GitHubProjectsClient

def main():
    token = os.getenv('GITHUB_TOKEN') or os.getenv('TEST_GITHUB_TOKEN')
    if not token:
        print("ERROR: GITHUB_TOKEN or TEST_GITHUB_TOKEN not found in environment")
        return
    
    print(f"Using token: {token[:4]}...{token[-4:]}")
    
    client = GitHubProjectsClient(token)
    
    # Test the viewer query
    query = """
    query GetViewerProjects($first: Int!) {
      viewer {
        login
        projectsV2(first: $first) {
          nodes {
            id
            title
            shortDescription
            readme
            url
            public
            createdAt
            updatedAt
            owner {
              ... on User {
                login
              }
              ... on Organization {
                login
              }
            }
          }
        }
      }
    }
    """
    
    try:
        result = client._execute_with_retry(query, {"first": 20})
        print("Raw result:")
        print(result)
        print("\nViewer login:", result.get("viewer", {}).get("login"))
        print("Number of projects:", len(result.get("viewer", {}).get("projectsV2", {}).get("nodes", [])))
        
        projects = result.get("viewer", {}).get("projectsV2", {}).get("nodes", [])
        for i, project in enumerate(projects):
            print(f"\nProject {i+1}:")
            print(f"  Title: {project.get('title')}")
            print(f"  ID: {project.get('id')}")
            print(f"  Owner: {project.get('owner', {}).get('login')}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()