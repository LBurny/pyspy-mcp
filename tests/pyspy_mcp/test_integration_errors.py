"""Integration tests for error handling paths."""

from __future__ import annotations

import pytest

from pyspy_mcp import tools


def test_dump_stacks_missing_pid_raises():
    """dump_stacks on a non-existent PID should raise a RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        tools.dump_stacks(pid=99999999)
    err = str(exc_info.value).lower()
    # py-spy typically reports a permission or process-not-found error.
    assert "failed" in err or "error" in err or "denied" in err


def test_record_profile_requires_pid_or_command():
    """record_profile must raise when neither pid nor command is given."""
    with pytest.raises(ValueError, match="pid or command"):
        tools.record_profile(duration=1)


def test_record_profile_rejects_both_pid_and_command():
    """record_profile must raise when both pid and command are given."""
    with pytest.raises(ValueError, match="not both"):
        tools.record_profile(pid=1234, command=["python", "x.py"], duration=1)


def test_record_profile_rejects_invalid_duration():
    """record_profile must reject non-positive durations."""
    with pytest.raises(ValueError, match="duration"):
        tools.record_profile(pid=1234, duration=0)


def test_analyze_profile_missing_file_raises():
    """analyze_profile must raise FileNotFoundError for a missing profile."""
    with pytest.raises(FileNotFoundError):
        tools.analyze_profile("/tmp/this_profile_does_not_exist.json")


def test_top_profile_requires_pid_or_command():
    """top_profile must raise when neither pid nor command is given."""
    with pytest.raises(ValueError, match="pid or command"):
        tools.top_profile(duration=1)
