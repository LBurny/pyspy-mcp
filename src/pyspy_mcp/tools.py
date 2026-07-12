"""Core tool implementations that drive py-spy."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from . import parser
from .process_util import PythonProcess, format_process_list, list_python_processes
from .py_spy_finder import find_py_spy


# Valid output formats supported by py-spy record.
VALID_FORMATS = {"flamegraph", "speedscope", "raw", "chrometrace"}


def _run_py_spy(args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run py-spy with the given arguments and return the completed process."""
    binary = find_py_spy()
    env = os.environ.copy()
    env.setdefault("RUST_LOG", "warn")
    env.setdefault("RUST_BACKTRACE", "1")
    return subprocess.run(
        [binary, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=timeout,
        check=False,
    )



def record_profile(
    pid: Optional[int] = None,
    command: Optional[List[str]] = None,
    duration: int = 5,
    output_format: str = "speedscope",
    rate: int = 100,
    native: bool = False,
    idle: bool = False,
    gil: bool = False,
    subprocesses: bool = False,
    output_path: Optional[str] = None,
) -> str:
    """Record a profile from a Python process or command.

    Returns the contents of the generated profile file as a string.
    """
    if output_format not in VALID_FORMATS:
        raise ValueError(f"Unsupported format: {output_format}. Use one of {VALID_FORMATS}")
    if not (pid or command):
        raise ValueError("Either pid or command must be provided")
    if pid and command:
        raise ValueError("Provide either pid or command, not both")
    if duration <= 0:
        raise ValueError("duration must be positive")

    if output_path:
        out = Path(output_path)
    else:
        suffix = ".svg" if output_format == "flamegraph" else ".json" if output_format in ("speedscope", "chrometrace") else ".txt"
        out = Path(tempfile.mkstemp(suffix=suffix, prefix="pyspy_")[1])

    args = [
        "record",
        "-o", str(out),
        "--format", output_format,
        "-d", str(duration),
        "-r", str(rate),
    ]
    if native:
        args.append("--native")
    if idle:
        args.append("--idle")
    if gil:
        args.append("--gil")
    if subprocesses:
        args.append("--subprocesses")

    if pid:
        args.extend(["--pid", str(pid)])
    else:
        args.append("--")
        args.extend(command)

    result = _run_py_spy(args, timeout=duration + 30)
    if result.returncode != 0:
        raise RuntimeError(
            f"py-spy record failed (exit {result.returncode}):\n{result.stderr}"
        )

    with open(out, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def dump_stacks(
    pid: int,
    json_output: bool = True,
    locals_level: int = 0,
    subprocesses: bool = False,
    native: bool = False,
) -> str:
    """Dump the current Python call stacks for a process."""
    if not (0 <= locals_level <= 2):
        raise ValueError("locals_level must be between 0 and 2")
    args = ["dump", "--pid", str(pid)]
    if json_output:
        args.append("--json")
    for _ in range(locals_level):
        args.append("--locals")
    if subprocesses:
        args.append("--subprocesses")
    if native:
        args.append("--native")

    result = _run_py_spy(args, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(
            f"py-spy dump failed (exit {result.returncode}):\n{result.stderr}"
        )
    return result.stdout


def list_python_processes_tool() -> str:
    """List running Python processes on this machine."""
    processes: List[PythonProcess] = list_python_processes()
    if not processes:
        return "No Python processes found."
    return format_process_list(processes)


def analyze_profile(profile_path: str, top_n: int = 10) -> str:
    """Analyze an existing profile file and return the hottest frames."""
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer")
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        frames = parser.analyze_speedscope(path, top_n=top_n)
    elif suffix == ".txt" or suffix == ".raw":
        frames = parser.parse_raw(path, top_n=top_n)
    else:
        # Best-effort: try speedscope first, then raw.
        try:
            frames = parser.analyze_speedscope(path, top_n=top_n)
        except Exception:
            frames = parser.parse_raw(path, top_n=top_n)

    if not frames:
        return "No samples found in profile."
    return parser.format_hot_frames(frames)


def compare_profiles(profile_a: str, profile_b: str, top_n: int = 10) -> str:
    """Compare two profiles and return a table of changes."""
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer")
    return parser.compare_profiles(profile_a, profile_b, top_n=top_n)


def top_profile(
    pid: Optional[int] = None,
    command: Optional[List[str]] = None,
    duration: int = 5,
    rate: int = 100,
    native: bool = False,
    idle: bool = False,
    gil: bool = False,
    subprocesses: bool = False,
    tail_lines: int = 40,
) -> str:
    """Run ``py-spy top`` for a short time and capture the final output.

    On Windows, ``py-spy top`` cannot be captured through a pipe, so we fall
    back to a short ``record --format raw`` sample and return the hottest frames.

    Args:
        pid: Process ID. Use this OR command.
        command: Command to run and monitor. Use this OR pid.
        duration: How many seconds to run top (default 5).
        rate: Samples per second (default 100).
        native: Include native frames if supported.
        idle: Include idle threads.
        gil: Only show traces holding the GIL.
        subprocesses: Include child processes.
        tail_lines: Number of trailing lines to return (default 40).

    Returns:
        The final top summary lines, or a hot-frame table on Windows.
    """
    if not (pid or command):
        raise ValueError("Either pid or command must be provided")
    if pid and command:
        raise ValueError("Provide either pid or command, not both")

    if sys.platform == "win32":
        return _top_profile_windows(
            pid=pid,
            command=command,
            duration=duration,
            rate=rate,
            native=native,
            idle=idle,
            gil=gil,
            subprocesses=subprocesses,
            top_n=tail_lines,
        )

    args = [
        "top",
        "-r", str(rate),
    ]
    if native:
        args.append("--native")
    if idle:
        args.append("--idle")
    if gil:
        args.append("--gil")
    if subprocesses:
        args.append("--subprocesses")

    if pid:
        args.extend(["--pid", str(pid)])
    else:
        args.append("--")
        args.extend(command)

    # top runs indefinitely; collect output for the requested duration then terminate.
    binary = find_py_spy()
    env = os.environ.copy()
    env.setdefault("RUST_LOG", "warn")
    proc = subprocess.Popen(
        [binary, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    from collections import deque
    import threading
    import time

    lines: deque[str] = deque(maxlen=tail_lines)

    def reader() -> None:
        try:
            for line in proc.stdout:
                lines.append(line.rstrip("\n"))
        except Exception:
            pass

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    time.sleep(duration)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

    reader_thread.join(timeout=5)

    if not lines and proc.stderr:
        return proc.stderr.read()
    return "\n".join(lines)


def _top_profile_windows(
    pid: Optional[int],
    command: Optional[List[str]],
    duration: int,
    rate: int,
    native: bool,
    idle: bool,
    gil: bool,
    subprocesses: bool,
    top_n: int,
) -> str:
    """Windows fallback for top_profile using a short raw recording."""
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="pyspy_top_")
    os.close(fd)
    try:
        args = [
            "record",
            "-o", path,
            "--format", "raw",
            "-d", str(duration),
            "-r", str(rate),
        ]
        if native:
            args.append("--native")
        if idle:
            args.append("--idle")
        if gil:
            args.append("--gil")
        if subprocesses:
            args.append("--subprocesses")

        if pid:
            args.extend(["--pid", str(pid)])
        else:
            args.append("--")
            args.extend(command)

        result = _run_py_spy(args, timeout=duration + 30)
        if result.returncode != 0:
            raise RuntimeError(
                f"py-spy top (Windows fallback) failed (exit {result.returncode}):\n{result.stderr}"
            )

        frames = parser.parse_raw(path, top_n=top_n)
        if not frames:
            return "No samples collected."
        return parser.format_hot_frames(frames)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

