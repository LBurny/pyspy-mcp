"""Utilities for cleaning up temporary files and subprocesses."""

from __future__ import annotations

import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Optional


@contextmanager
def temp_file(suffix: str = "", prefix: str = "pyspy_") -> Iterator[Path]:
    """Create a temporary file and delete it on exit."""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    file_path = Path(path)
    try:
        yield file_path
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass


@contextmanager
def managed_subprocess(
    args: List[str],
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.PIPE,
    text: bool = True,
    encoding: str = "utf-8",
    errors: str = "replace",
    env: Optional[Dict[str, str]] = None,
) -> Iterator[subprocess.Popen]:
    """Run a subprocess and ensure it is terminated on exit."""
    proc = subprocess.Popen(
        args,
        stdout=stdout,
        stderr=stderr,
        text=text,
        encoding=encoding,
        errors=errors,
        env=env,
    )
    try:
        yield proc
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
