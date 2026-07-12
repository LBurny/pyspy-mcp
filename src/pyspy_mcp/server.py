"""FastMCP server exposing py-spy based Python performance tools."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import List, Optional

from fastmcp import FastMCP

from . import tools
from .__init__ import __version__
from .process_util import list_python_processes as _list_python_processes
from .py_spy_finder import find_py_spy


logger = logging.getLogger(__name__)

mcp = FastMCP(
    "pyspy-mcp",
    instructions=(
        "A Python performance profiling assistant powered by py-spy. "
        "Recommended workflow: "
        "1) call list_python_processes to discover candidate Python processes; "
        "2) use record_profile to sample a target PID or command; "
        "3) use analyze_profile or compare_profiles to inspect results. "
        "Profiling may require elevated permissions (ptrace on Linux, root on macOS, Administrator on Windows). "
        "When comparing two runs, generate both profiles with the same duration and rate."
    ),
)


def setup_logging(verbose: bool) -> None:
    """Configure root logging level for the server."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for the server entry point."""
    parser = argparse.ArgumentParser(
        prog="pyspy-mcp",
        description="MCP server for Python performance profiling with py-spy",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port when using --transport http (default: 8080)",
    )
    return parser.parse_args(argv)


@mcp.tool(annotations={"destructiveHint": True})
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
) -> str:
    """Record a sampling profile of a Python process or command.

    Typical workflow:
        1. list_python_processes() -> pick a target PID
        2. record_profile(pid=..., duration=10, output_format="speedscope")
        3. analyze_profile(profile_path=...) -> hottest frames

    Args:
        pid: Process ID to sample. Use this OR command, not both.
        command: Command to run and sample, e.g. ["python", "script.py"]. Use this OR pid.
        duration: How many seconds to sample (default 5, recommended 5-60).
        output_format: One of "speedscope" (JSON), "flamegraph" (SVG), "raw" (text), "chrometrace".
        rate: Samples per second (default 100).
        native: Include native/C extension frames if supported on this platform.
        idle: Include idle threads.
        gil: Only include traces holding the GIL.
        subprocesses: Include child Python processes.

    Returns:
        The generated profile content (JSON, SVG, or raw text).
    """
    return tools.record_profile(
        pid=pid,
        command=command,
        duration=duration,
        output_format=output_format,
        rate=rate,
        native=native,
        idle=idle,
        gil=gil,
        subprocesses=subprocesses,
    )


@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def dump_stacks(
    pid: int,
    json_output: bool = True,
    locals_level: int = 0,
    subprocesses: bool = False,
    native: bool = False,
) -> str:
    """Dump the current Python call stacks of a process.

    Args:
        pid: Process ID to inspect.
        json_output: Return structured JSON instead of human-readable text.
        locals_level: Number of times to pass --locals (0-2). Each level shows more locals.
        subprocesses: Include child Python processes.
        native: Include native frames if supported.

    Returns:
        The stack dump as JSON or text.
    """
    return tools.dump_stacks(
        pid=pid,
        json_output=json_output,
        locals_level=locals_level,
        subprocesses=subprocesses,
        native=native,
    )


@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def list_python_processes() -> str:
    """List running Python processes on this machine.

    Returns:
        A table of PID, memory usage, and command line.
    """
    return tools.list_python_processes_tool()


@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def analyze_profile(profile_path: str, top_n: int = 10) -> str:
    """Analyze an existing py-spy profile and return the hottest frames.

    Args:
        profile_path: Path to a speedscope JSON (.json) or raw (.txt) profile.
        top_n: Number of top frames to return (default 10).

    Returns:
        A Markdown table of hot frames with sample counts and percentages.
    """
    return tools.analyze_profile(profile_path, top_n=top_n)


@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def compare_profiles(profile_a: str, profile_b: str, top_n: int = 10) -> str:
    """Compare two speedscope profiles and show percentage changes.

    Args:
        profile_a: Path to the first profile.
        profile_b: Path to the second profile.
        top_n: Number of frames to show (default 10).

    Returns:
        A Markdown table showing the percentage of time in each profile and the delta.
    """
    return tools.compare_profiles(profile_a, profile_b, top_n=top_n)


@mcp.tool(annotations={"destructiveHint": True})
def top_profile(
    pid: Optional[int] = None,
    command: Optional[List[str]] = None,
    duration: int = 5,
    rate: int = 100,
    native: bool = False,
    idle: bool = False,
    gil: bool = False,
    subprocesses: bool = False,
) -> str:
    """Run a live ``py-spy top`` view for a few seconds and return the summary.

    On Windows, ``py-spy top`` cannot be captured through a pipe, so this tool
    falls back to a short ``record --format raw`` sample and returns the hottest
    frames instead of raw top output.

    Args:
        pid: Process ID. Use this OR command.
        command: Command to run and monitor. Use this OR pid.
        duration: How many seconds to run top (default 5, recommended 5-60).
        rate: Samples per second (default 100).
        native: Include native frames if supported.
        idle: Include idle threads.
        gil: Only show traces holding the GIL.
        subprocesses: Include child processes.

    Returns:
        The final top summary lines, or a hot-frame table on Windows.
    """
    return tools.top_profile(
        pid=pid,
        command=command,
        duration=duration,
        rate=rate,
        native=native,
        idle=idle,
        gil=gil,
        subprocesses=subprocesses,
    )


@mcp.resource("python://processes")
def python_processes_resource() -> str:
    """Return a JSON list of currently running Python processes."""
    processes = _list_python_processes()
    return json.dumps(
        [
            {
                "pid": p.pid,
                "cmdline": p.cmdline,
                "create_time": p.create_time,
                "username": p.username,
                "memory_mb": round(p.memory_mb, 2),
            }
            for p in processes
        ],
        ensure_ascii=False,
        indent=2,
    )


def main() -> None:
    """Entry point used by the ``pyspy-mcp`` console script."""
    args = parse_args()
    setup_logging(args.verbose)
    logger.info("Starting pyspy-mcp v%s", __version__)
    try:
        logger.info("Resolved py-spy binary: %s", find_py_spy())
    except FileNotFoundError as exc:
        logger.warning("Could not resolve py-spy binary: %s", exc)
    mcp.run(transport=args.transport, port=args.port)


if __name__ == "__main__":
    main()
