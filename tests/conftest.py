"""Pytest configuration for CatchUp tests."""
import pytest
import os


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "unit: Fast unit tests with no I/O"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests with local files only (no network)"
    )
    config.addinivalue_line(
        "markers",
        "live: Live tests that make real API calls (requires RUN_LIVE_TESTS=1)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip live tests unless RUN_LIVE_TESTS=1.

    This provides an extra safety layer.
    """
    if os.environ.get('RUN_LIVE_TESTS') != '1':
        skip_live = pytest.mark.skip(reason="Live tests require RUN_LIVE_TESTS=1")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def enforce_network_guard():
    """
    Enforce NetworkGuard for all non-live tests.

    This catches accidental network calls.
    """
    import sys
    from pathlib import Path

    # Add tests directory to path
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir))

    # Only apply to non-live tests
    if os.environ.get('RUN_LIVE_TESTS') != '1':
        from utils import NetworkGuard
        with NetworkGuard():
            yield
    else:
        yield
