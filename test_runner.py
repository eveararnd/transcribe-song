#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Runner Script for Parakeet TDT Deployment

Usage:
    python test_runner.py [options]
    
Options:
    --all        Run all tests (default)
    --unit       Run unit tests only
    --system     Run system tests only
    --model      Run model tests only
    --ui         Run UI tests only
    --component  Run component tests only
    --coverage   Generate coverage report
    --verbose    Verbose output
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Ensure we're in the right directory
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True)
    success = result.returncode == 0
    
    if success:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED")
    
    return success

def run_python_tests(test_type, coverage=False, verbose=False):
    """Run Python tests with pytest"""
    # Use the virtual environment's Python directly
    python_bin = "/home/davegornshtein/parakeet-env/bin/python"
    
    pytest_cmd = f"{python_bin} -m pytest"
    
    # Add test directory
    if test_type == "all":
        pytest_cmd += " tests/"
    elif test_type == "unit":
        pytest_cmd += " tests/unit/"
    elif test_type == "system":
        pytest_cmd += " tests/system/"
    elif test_type == "model":
        pytest_cmd += " tests/model/"
    elif test_type == "component":
        pytest_cmd += " tests/component/"
    
    # Add options
    if verbose:
        pytest_cmd += " -v"
    if coverage:
        pytest_cmd += " --cov=src --cov-report=html --cov-report=term"
    
    pytest_cmd += " --tb=short"
    
    return run_command(pytest_cmd, f"Python {test_type} tests")

def run_ui_tests():
    """Run UI tests with npm"""
    cmd = "cd music-analyzer-frontend && npm test -- --run"
    return run_command(cmd, "UI tests")

def main():
    parser = argparse.ArgumentParser(description="Test runner for Parakeet TDT Deployment")
    
    # Test type arguments
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--system", action="store_true", help="Run system tests only")
    parser.add_argument("--model", action="store_true", help="Run model tests only")
    parser.add_argument("--ui", action="store_true", help="Run UI tests only")
    parser.add_argument("--component", action="store_true", help="Run component tests only")
    
    # Options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # If no specific test type is selected, run all
    if not any([args.unit, args.system, args.model, args.ui, args.component]):
        args.all = True
    
    results = []
    
    # Run selected tests
    if args.all or args.unit:
        results.append(("Unit Tests", run_python_tests("unit", args.coverage, args.verbose)))
    
    if args.all or args.system:
        results.append(("System Tests", run_python_tests("system", args.coverage, args.verbose)))
    
    if args.all or args.component:
        results.append(("Component Tests", run_python_tests("component", args.coverage, args.verbose)))
    
    if args.all or args.model:
        print("\n⚠️  Model tests require significant GPU memory and may fail on systems with limited resources")
        results.append(("Model Tests", run_python_tests("model", args.coverage, args.verbose)))
    
    if args.all or args.ui:
        results.append(("UI Tests", run_ui_tests()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("-"*60)
    print(f"Total: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test suite(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())