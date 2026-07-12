from __future__ import annotations

import subprocess

import pytest

from pyspy_mcp.errors import PySpyError, map_subprocess_error


def _make_result(returncode: int, stderr: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["py-spy", "record", "--pid", "1"],
        returncode=returncode,
        stdout="",
        stderr=stderr,
    )


def test_permission_denied_error():
    result = _make_result(1, "Error: permission denied")
    err = map_subprocess_error(result, "record")
    assert err.error_type == "permission_denied"
    assert "sudo" in err.hint or "Administrator" in err.hint


def test_process_not_found_error():
    result = _make_result(1, "Error: no such process (pid=1)")
    err = map_subprocess_error(result, "record")
    assert err.error_type == "process_not_found"


def test_timeout_error():
    result = _make_result(-9, "killed")
    err = map_subprocess_error(result, "record")
    assert err.error_type == "timeout"


def test_unknown_error():
    result = _make_result(1, "some unexpected failure")
    err = map_subprocess_error(result, "record")
    assert err.error_type == "unknown"


def test_error_response_json():
    err = PySpyError("permission_denied", "failed", "use sudo")
    response = err.to_response()
    assert '"status": "error"' in response
    assert '"error_type": "permission_denied"' in response
