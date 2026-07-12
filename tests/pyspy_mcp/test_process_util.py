"""Tests for process listing utilities."""

from __future__ import annotations

import os
from unittest import mock

from pyspy_mcp import process_util


def test_is_python_process_detects_python_in_name():
    assert process_util._is_python_process("python3.11", [])
    assert process_util._is_python_process("python.exe", [])
    assert process_util._is_python_process("Python", [])


def test_is_python_process_detects_python_in_cmdline():
    assert process_util._is_python_process("myapp", ["/usr/bin/python3", "script.py"])
    assert process_util._is_python_process("", ["python", "script.py"])


def test_is_python_process_rejects_non_python():
    assert not process_util._is_python_process("node", ["node", "app.js"])
    assert not process_util._is_python_process("bash", ["bash", "script.sh"])
    assert not process_util._is_python_process("", [])


def test_list_python_processes_includes_current_process():
    """The current Python process should appear in the list."""
    processes = process_util.list_python_processes()
    pids = {p.pid for p in processes}
    assert os.getpid() in pids


def test_list_python_processes_skips_inaccessible(monkeypatch):
    """AccessDenied and NoSuchProcess exceptions should not crash the listing."""

    class FakeInfo:
        """Dict-like info object that raises on memory_info access."""

        def __init__(self):
            self._data = {
                "pid": 1234,
                "name": "python3",
                "cmdline": ["python3"],
                "create_time": 0,
                "username": None,
            }

        def __getitem__(self, key):
            if key == "memory_info":
                raise process_util.psutil.NoSuchProcess(1234)
            return self._data[key]

        def get(self, key, default=None):
            if key == "memory_info":
                raise process_util.psutil.NoSuchProcess(1234)
            return self._data.get(key, default)

    class FakeProc:
        def __init__(self):
            self.info = FakeInfo()

    with monkeypatch.context() as m:
        m.setattr(process_util.psutil, "process_iter", lambda attrs=None: iter([FakeProc()]))
        processes = process_util.list_python_processes()
        assert 1234 not in {p.pid for p in processes}


def test_format_process_list_is_deterministic_shape():
    """Output should have a header and one line per process."""
    processes = [
        process_util.PythonProcess(pid=1, cmdline="python a.py", create_time=0, username=None, memory_mb=12.5),
        process_util.PythonProcess(pid=2, cmdline="python b.py", create_time=0, username=None, memory_mb=34.0),
    ]
    text = process_util.format_process_list(processes, max_count=10)
    lines = text.splitlines()
    assert len(lines) == 3  # header + 2 processes
    assert "PID" in lines[0]
    assert "python a.py" in lines[1]
    assert "python b.py" in lines[2]


def test_format_process_list_truncates():
    """max_count limits the number of returned rows."""
    processes = [
        process_util.PythonProcess(pid=i, cmdline=f"python {i}.py", create_time=0, username=None, memory_mb=float(i))
        for i in range(10)
    ]
    text = process_util.format_process_list(processes, max_count=3)
    lines = text.splitlines()
    assert len(lines) == 4  # header + 3 rows
