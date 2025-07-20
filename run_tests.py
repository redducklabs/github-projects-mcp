#!/usr/bin/env python3
"""
Test runner script for local development
Usage: python run_tests.py [--fast] [--integration] [--canary]
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run tests for GitHub Projects MCP Server")
    parser.add_argument("--fast", action="store_true", help="Skip slow integration tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--canary", action="store_true", help="Run only canary test")
    parser.add_argument("--no-lint", action="store_true", help="Skip linting checks")
    parser.add_argument("--no-type", action="store_true", help="Skip type checking")
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 GitHub Projects MCP Server Test Runner")
    print(f"📁 Working directory: {project_root}")
    
    # Check if .env.test exists
    if not os.path.exists(".env.test"):
        print("⚠️  Warning: .env.test not found. Some tests may be skipped.")
        print("   Copy .env.test.template and fill in your test configuration.")
    
    success = True
    
    # Install in development mode
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], "Installing package in development mode"):
        return 1
    
    # Code quality checks
    if not args.no_lint:
        print("\n📝 Code Quality Checks")
        success &= run_command([
            "flake8", "github_projects_mcp/", 
            "--count", "--select=E9,F63,F7,F82", 
            "--show-source", "--statistics"
        ], "Critical linting checks", check=False)
        
        success &= run_command([
            "flake8", "github_projects_mcp/", 
            "--count", "--max-complexity=10", 
            "--max-line-length=120", "--statistics"
        ], "Code style checks", check=False)
    
    # Type checking
    if not args.no_type:
        success &= run_command([
            "mypy", "github_projects_mcp/", 
            "--ignore-missing-imports"
        ], "Type checking", check=False)
    
    # Test execution
    print("\n🧪 Running Tests")
    
    if args.canary:
        # Only canary test
        success &= run_command([
            sys.executable, "-m", "pytest", 
            "tests/test_canary.py", "-v", "-s"
        ], "Canary test (live integration)")
    
    elif args.integration:
        # Only integration tests  
        success &= run_command([
            sys.executable, "-m", "pytest", 
            "tests/test_live_integration.py", 
            "tests/test_canary.py", "-v"
        ], "Integration tests")
    
    elif args.fast:
        # Skip slow tests
        success &= run_command([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short",
            "-k", "not (live_integration or canary)"
        ], "Fast test suite (unit tests only)")
    
    else:
        # Full test suite
        success &= run_command([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short", "--durations=10"
        ], "Full test suite")
    
    # Summary
    print("\n" + "="*50)
    if success:
        print("🎉 All checks passed!")
        return 0
    else:
        print("❌ Some checks failed. See output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())