from __future__ import annotations

import subprocess
import sys

from pyspy_mcp.cleanup import managed_subprocess, temp_file


def test_temp_file_is_deleted():
    with temp_file(suffix=".txt") as path:
        assert path.exists()
        path.write_text("hello")
    assert not path.exists()


def test_temp_file_missing_ok_on_cleanup():
    with temp_file(suffix=".txt") as path:
        path.unlink()
    # Should not raise


def test_managed_subprocess_terminates():
    # Use a command that sleeps long enough to be interrupted.
    with managed_subprocess([sys.executable, "-c", "import time; time.sleep(10)"]) as proc:
        assert proc.poll() is None
    assert proc.poll() is not None


def test_managed_subprocess_returns_pipe():
    with managed_subprocess([sys.executable, "-c", "print('ok')"]) as proc:
        stdout, _ = proc.communicate(timeout=5)
    assert stdout.strip() == "ok"
