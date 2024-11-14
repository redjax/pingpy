from __future__ import annotations

import logging
from unittest import mock

from pingpy.main import _ping_target

import pytest

@pytest.fixture
def mock_subprocess_run():
    """Fixture to mock subprocess.run."""
    with mock.patch("subprocess.run") as mock_run:
        yield mock_run

@pytest.fixture
def mock_platform_system():
    """Fixture to mock platform.system."""
    with mock.patch("platform.system") as mock_platform:
        yield mock_platform

def test_ping_target_success(mock_subprocess_run, mock_platform_system, caplog):
    """Test successful ping response (mocking subprocess)."""
    # Mock platform to return 'windows'
    mock_platform_system.return_value = 'Windows'

    # Mock subprocess.run to simulate a successful ping response
    mock_subprocess_run.return_value = mock.Mock(stdout="Reply from 192.168.1.1: bytes=32 time=1ms TTL=64", stderr="")

    # Run the ping target function with caplog capturing logs at INFO level
    with caplog.at_level(logging.INFO):
        _ping_target("192.168.1.1", repeat=1, verbose=True)

    # Verify that logging occurs as expected
    assert "Reply from 192.168.1.1 - Success" in caplog.text
