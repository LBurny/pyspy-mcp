"""Integration tests for the top_profile tool."""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest

from pyspy_mcp import tools


BUSYLOOP = os.path.join(os.path.dirname(__file__), "..", "scripts", "busyloop.py")


@pytest.fixture
def busyloop_process():
    """Run busyloop.py as a subprocess and clean it up after the test."""
    proc = subprocess.Popen(
        [sys.executable, BUSYLOOP],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_top_profile_returns_within_duration(busyloop_process):
    """top_profile should start, run for the requested duration, and stop."""
    start = time.time()
    result = tools.top_profile(
        pid=busyloop_process.pid,
        duration=2,
        rate=100,
    )
    elapsed = time.time() - start
    # Allow some overhead for startup/shutdown.
    assert elapsed < 10
    assert isinstance(result, str)


def test_top_profile_mentions_target_function(busyloop_process):
    """top_profile output should mention the function being executed."""
    result = tools.top_profile(
        pid=busyloop_process.pid,
        duration=2,
        rate=100,
    )
    lowered = result.lower()
    assert "busyloop" in lowered or "<module>" in lowered or "busy" in lowered


def test_top_profile_with_command():
    """top_profile can also be invoked with a command instead of a pid."""
    result = tools.top_profile(
        command=[sys.executable, BUSYLOOP],
        duration=2,
        rate=100,
    )
    assert isinstance(result, str)
    # The output is a snapshot of top; just verify it does not error out.
    assert "error" not in result.lower() or "py-spy" not in result.lower()
