"""End-to-end integration tests for the py-spy MCP server tools."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
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
    time.sleep(0.5)  # Let Python initialize before sampling.
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_record_and_analyze_profile(busyloop_process):
    """Record a speedscope profile of a running Python process and analyze it."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = tools.record_profile(
            pid=busyloop_process.pid,
            duration=2,
            output_format="speedscope",
            rate=100,
            output_path=output_path,
        )
        assert result  # returns file content
        assert os.path.getsize(output_path) > 0

        analysis = tools.analyze_profile(output_path, top_n=5)
        assert "busyloop" in analysis.lower() or "<module>" in analysis.lower()
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_dump_stacks(busyloop_process):
    """Dump current stacks from a running Python process."""
    result = tools.dump_stacks(pid=busyloop_process.pid, json_output=True)
    data = __import__("json").loads(result)
    assert isinstance(data, list)
    assert len(data) >= 1
    # At least one thread should contain the busyloop frame.
    all_names = {
        frame["name"]
        for trace in data
        for frame in trace.get("frames", [])
    }
    assert "busyloop" in all_names or "<module>" in all_names


def test_list_python_processes():
    """The process list should include the current Python interpreter."""
    result = tools.list_python_processes_tool()
    assert str(os.getpid()) in result
    assert sys.executable.replace("\\", "/") in result.replace("\\", "/") or "python" in result.lower()
