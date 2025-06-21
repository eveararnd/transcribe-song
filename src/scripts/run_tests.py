#!/usr/bin/env python3
"""
Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.

Comprehensive test runner for Music Analyzer V2
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

# Ensure we're using the right venv
VENV_PATH = "/home/davegornshtein/parakeet-env"
if not sys.prefix == VENV_PATH:
    print(f"Activating virtual environment: {VENV_PATH}")
    activate_script = os.path.join(VENV_PATH, "bin", "activate")
    exec(open(activate_script).read(), {'__file__': activate_script})

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd)
    return result.returncode == 0

def run_python_tests(test_type=None, verbose=False, coverage=False):
    """Run Python tests"""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Add specific test directory or marker
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "component":
        cmd.append("tests/component/")
    elif test_type == "system":
        cmd.append("tests/system/")
    elif test_type == "model":
        cmd.append("tests/model/")
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "all":
        cmd.append("tests/")
    else:
        cmd.append("tests/")
    
    return run_command(cmd)

def run_ui_tests(coverage=False):
    """Run UI tests"""
    frontend_dir = Path(__file__).parent / "music-analyzer-frontend"
    
    if not frontend_dir.exists():
        print(f"Frontend directory not found: {frontend_dir}")
        return False
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        if not run_command("npm install", cwd=frontend_dir):
            return False
    
    # Run tests
    cmd = "npm test -- --run"
    if coverage:
        cmd += " --coverage"
    
    return run_command(cmd, cwd=frontend_dir)

def run_all_tests(verbose=False, coverage=False):
    """Run all tests"""
    results = {}
    
    # Python tests
    print("\n🐍 Running Python tests...")
    test_types = ["unit", "component", "system", "model"]
    
    for test_type in test_types:
        print(f"\n📦 Running {test_type} tests...")
        results[f"python_{test_type}"] = run_python_tests(test_type, verbose, coverage)
    
    # UI tests
    print("\n🎨 Running UI tests...")
    results["ui"] = run_ui_tests(coverage)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total

def main():
    parser = argparse.ArgumentParser(description="Run Music Analyzer tests")
    parser.add_argument(
        "type",
        nargs="?",
        default="all",
        choices=["all", "unit", "component", "system", "model", "ui", "fast"],
        help="Type of tests to run (default: all)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--no-timeout", action="store_true", help="Disable timeouts")
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["USE_TF"] = "0"
    os.environ["USE_TORCH"] = "1"
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
    
    if args.no_timeout:
        os.environ["PYTEST_TIMEOUT"] = "0"
    
    # Run tests based on type
    success = False
    
    if args.type == "all":
        success = run_all_tests(args.verbose, args.coverage)
    elif args.type == "ui":
        success = run_ui_tests(args.coverage)
    else:
        success = run_python_tests(args.type, args.verbose, args.coverage)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()