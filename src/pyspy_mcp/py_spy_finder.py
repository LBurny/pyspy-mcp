"""Locate the py-spy binary used by this MCP server."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def _binary_name() -> str:
    return "py-spy.exe" if platform.system() == "Windows" else "py-spy"


def _development_binary() -> Path | None:
    """Look for a binary built from the sibling Rust workspace."""
    # __file__ = I:/pyspy_mcp/src/pyspy_mcp/py_spy_finder.py
    workspace_root = Path(__file__).resolve().parent.parent.parent
    candidate = workspace_root / "target" / "release" / _binary_name()
    if candidate.exists():
        return candidate
    return None


def _bundled_binary() -> Path | None:
    """Look for a binary shipped inside this Python package."""
    package_dir = Path(__file__).resolve().parent
    candidate = package_dir / "bin" / _binary_name()
    if candidate.exists():
        return candidate
    return None


def find_py_spy() -> str:
    """Return the path to the py-spy binary.

    Resolution order:
    1. ``PYSPY_MCP_BINARY`` environment variable.
    2. A binary built in the sibling Rust workspace (``target/release``).
    3. A binary bundled inside this package.
    4. ``py-spy`` on ``PATH``.

    Raises:
        FileNotFoundError: if no py-spy binary can be found.
    """
    env_binary = os.environ.get("PYSPY_MCP_BINARY")
    if env_binary:
        path = Path(env_binary)
        if path.exists():
            return str(path)
        raise FileNotFoundError(
            f"PYSPY_MCP_BINARY points to a missing file: {env_binary}"
        )

    dev = _development_binary()
    if dev:
        return str(dev)

    bundled = _bundled_binary()
    if bundled:
        return str(bundled)

    path_binary = shutil.which("py-spy")
    if path_binary:
        return path_binary

    raise FileNotFoundError(
        "Could not find a py-spy binary. Set PYSPY_MCP_BINARY, "
        "install py-spy on PATH, or build the Rust workspace first."
    )


if __name__ == "__main__":
    print(find_py_spy())
