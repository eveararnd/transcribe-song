"""
Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.

Pytest configuration file
"""
import sys
import os
import pytest
import pytest_asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ['USE_TF'] = '0'
os.environ['USE_TORCH'] = '1'
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'

# Configure pytest-asyncio
pytest_asyncio.fixture(scope="function")

# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "component: Component tests")
    config.addinivalue_line("markers", "system: System integration tests")
    config.addinivalue_line("markers", "model: Model-specific tests")
    config.addinivalue_line("markers", "slow: Slow tests that load models")
    config.addinivalue_line("markers", "timeout: Tests with custom timeout")

# Add timeout for model tests
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add timeouts"""
    for item in items:
        # Add timeout for model tests
        if "model" in str(item.fspath):
            item.add_marker(pytest.mark.timeout(600))
        # Mark slow tests
        if any(name in item.name for name in ["load", "model", "gemma", "phi4"]):
            item.add_marker(pytest.mark.slow)