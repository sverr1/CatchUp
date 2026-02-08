"""Test utilities for CatchUp."""
import socket
import sys
from unittest.mock import MagicMock
from typing import Any


class NetworkGuard:
    """
    Prevents network access during tests.

    Usage:
        with NetworkGuard():
            # code that should not make network calls
            ...
    """

    def __init__(self):
        self.original_socket = None
        self.original_getaddrinfo = None

    def __enter__(self):
        """Block network access."""
        # Store originals
        self.original_socket = socket.socket
        self.original_getaddrinfo = socket.getaddrinfo

        # Replace with mocks that raise
        def guard_socket(*args, **kwargs):
            raise RuntimeError(
                "❌ NetworkGuard: Attempted to create socket! "
                "Tests should not make network calls. "
                "Use fake clients or mark test with @pytest.mark.live"
            )

        def guard_getaddrinfo(*args, **kwargs):
            raise RuntimeError(
                "❌ NetworkGuard: Attempted DNS lookup! "
                "Tests should not make network calls. "
                "Use fake clients or mark test with @pytest.mark.live"
            )

        socket.socket = guard_socket
        socket.getaddrinfo = guard_getaddrinfo

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore network access."""
        socket.socket = self.original_socket
        socket.getaddrinfo = self.original_getaddrinfo


def assert_no_network_calls(func):
    """
    Decorator to ensure a test function makes no network calls.

    Usage:
        @assert_no_network_calls
        def test_something():
            ...
    """
    def wrapper(*args, **kwargs):
        with NetworkGuard():
            return func(*args, **kwargs)
    return wrapper
