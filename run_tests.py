#!/usr/bin/env python3
"""
Comprehensive test runner for Discord Summarize Bot
Runs all tests and generates reports
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔍 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def run_tests(test_type="all"):
    """Run different types of tests."""
    print("🧪 Discord Summarize Bot - Test Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run from the project root.")
        return False
    
    # Install test dependencies if needed
    if not Path("tests").exists():
        print("❌ Error: tests directory not found.")
        return False
    
    all_passed = True
    
    if test_type in ["all", "unit"]:
        print("\n📋 Running Unit Tests...")
        success = run_command(
            "python -m pytest tests/unit/ -v --cov=main --cov-report=term-missing",
            "Unit Tests"
        )
        all_passed = all_passed and success
    
    if test_type in ["all", "integration"]:
        print("\n📋 Running Integration Tests...")
        success = run_command(
            "python -m pytest tests/integration/ -v",
            "Integration Tests"
        )
        all_passed = all_passed and success
    
    if test_type in ["all", "coverage"]:
        print("\n📋 Generating Coverage Report...")
        success = run_command(
            "python -m pytest tests/ --cov=main --cov-report=html --cov-report=xml",
            "Coverage Report"
        )
        all_passed = all_passed and success
    
    if test_type in ["all", "lint"]:
        print("\n📋 Running Code Quality Checks...")
        
        # Check if tools are installed
        try:
            import black
            success = run_command("black --check main.py test_local.py", "Code Formatting (Black)")
            all_passed = all_passed and success
        except ImportError:
            print("⚠️  Black not installed, skipping code formatting check")
        
        try:
            import flake8
            success = run_command("flake8 main.py test_local.py --max-line-length=88", "Linting (Flake8)")
            all_passed = all_passed and success
        except ImportError:
            print("⚠️  Flake8 not installed, skipping linting check")
    
    if test_type in ["all", "security"]:
        print("\n📋 Running Security Checks...")
        
        try:
            import bandit
            success = run_command("bandit -r main.py -f json -o bandit-report.json", "Security Scan (Bandit)")
            all_passed = all_passed and success
        except ImportError:
            print("⚠️  Bandit not installed, skipping security scan")
    
    if test_type in ["all", "docker"]:
        print("\n📋 Testing Docker Build...")
        success = run_command("docker build -t discord-summarize-bot:test .", "Docker Build")
        all_passed = all_passed and success
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests for Discord Summarize Bot")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "coverage", "lint", "security", "docker"],
        default="all",
        help="Type of tests to run"
    )
    
    args = parser.parse_args()
    
    success = run_tests(args.type)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
