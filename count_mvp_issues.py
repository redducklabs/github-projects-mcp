#!/usr/bin/env python3
"""Script to count MVP milestone issues in TherapyLink project"""

import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment
load_dotenv()

from github_projects_mcp.core.client import GitHubProjectsClient

def count_mvp_issues():
    token = os.getenv('GITHUB_TOKEN') or os.getenv('TEST_GITHUB_TOKEN')
    if not token:
        print("ERROR: GITHUB_TOKEN or TEST_GITHUB_TOKEN not found in environment")
        return
    
    client = GitHubProjectsClient(token)
    project_id = "PVT_kwDOCdCYe84A-G7b"  # TherapyLink Roadmap
    
    # Get all project items in batches
    all_items = []
    cursor = None
    
    while True:
        query = """
        query GetProjectItems($id: ID!, $first: Int!, $after: String) {
          node(id: $id) {
            ... on ProjectV2 {
              items(first: $first, after: $after) {
                pageInfo {
                  hasNextPage
                  endCursor
                }
                nodes {
                  id
                  content {
                    ... on Issue {
                      title
                      number
                    }
                  }
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldMilestoneValue {
                        milestone {
                          id
                          title
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {"id": project_id, "first": 50}
        if cursor:
            variables["after"] = cursor
        
        result = client._execute_with_retry(query, variables)
        items_data = result["node"]["items"]
        all_items.extend(items_data["nodes"])
        
        if not items_data["pageInfo"]["hasNextPage"]:
            break
        cursor = items_data["pageInfo"]["endCursor"]
    
    # Count MVP issues
    mvp_count = 0
    total_count = len(all_items)
    
    for item in all_items:
        # Check if any field value is a milestone with title "MVP"
        for field_value in item.get("fieldValues", {}).get("nodes", []):
            if "milestone" in field_value and field_value["milestone"]["title"] == "MVP":
                mvp_count += 1
                break
    
    print(f"TherapyLink Roadmap Project:")
    print(f"Total issues: {total_count}")
    print(f"MVP milestone issues: {mvp_count}")
    print(f"Non-MVP issues: {total_count - mvp_count}")

if __name__ == "__main__":
    count_mvp_issues()