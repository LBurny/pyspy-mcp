"""Utilities for finding Python processes on the local machine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import psutil


@dataclass
class PythonProcess:
    pid: int
    cmdline: str
    create_time: float
    username: str | None
    memory_mb: float


def list_python_processes() -> List[PythonProcess]:
    """Return a list of running processes whose executable looks like Python."""
    processes: List[PythonProcess] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time", "username", "memory_info"]):
        try:
            name = proc.info["name"] or ""
            cmdline = proc.info["cmdline"] or []
            cmdline_str = " ".join(cmdline) if cmdline else name
            if not _is_python_process(name, cmdline):
                continue
            mem = proc.info.get("memory_info")
            processes.append(
                PythonProcess(
                    pid=proc.info["pid"],
                    cmdline=cmdline_str,
                    create_time=proc.info["create_time"] or 0.0,
                    username=proc.info.get("username"),
                    memory_mb=(mem.rss / (1024 * 1024)) if mem else 0.0,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


def _is_python_process(name: str, cmdline: List[str]) -> bool:
    """Heuristic to decide whether a process is a Python interpreter."""
    lowered = name.lower()
    if "python" in lowered:
        return True
    if not cmdline:
        return False
    first = cmdline[0].lower()
    # Handle cases like /usr/bin/python3.11 or python.exe
    if "python" in first:
        return True
    return False


def format_process_list(processes: List[PythonProcess], max_count: int = 50) -> str:
    """Format a list of Python processes as a human-readable table."""
    lines = ["PID\tMemory(MB)\tCommand"]
    for p in processes[:max_count]:
        lines.append(f"{p.pid}\t{p.memory_mb:.1f}\t\t{p.cmdline[:120]}")
    return "\n".join(lines)
