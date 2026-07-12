"""Structured error handling for pyspy-mcp."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class PySpyError(RuntimeError):
    """Exception carrying a structured error response."""

    error_type: str
    message: str
    hint: str = ""
    command: Optional[str] = None

    def to_response(self) -> str:
        """Return a JSON string suitable for MCP tool output."""
        payload = {
            "status": "error",
            "error_type": self.error_type,
            "message": self.message,
            "hint": self.hint,
        }
        if self.command is not None:
            payload["command"] = self.command
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def __str__(self) -> str:
        return self.to_response()


def _stderr(result: subprocess.CompletedProcess) -> str:
    return (result.stderr or "").lower()


def map_subprocess_error(result: subprocess.CompletedProcess, action: str) -> PySpyError:
    """Map a py-spy subprocess failure to a structured error."""
    stderr = _stderr(result)
    returncode = result.returncode
    command = " ".join(str(a) for a in result.args) if result.args else None

    if any(
        phrase in stderr
        for phrase in (
            "permission denied",
            "access is denied",
            "could not read process memory",
        )
    ):
        return PySpyError(
            error_type="permission_denied",
            message=f"py-spy {action} failed: permission denied (exit {returncode}).",
            hint=(
                "On Linux use sudo or set cap_sys_ptrace; on macOS run as root; "
                "on Windows run as Administrator."
            ),
            command=command,
        )

    if "no such process" in stderr or ("process" in stderr and "not found" in stderr):
        return PySpyError(
            error_type="process_not_found",
            message=f"py-spy {action} failed: target process not found (exit {returncode}).",
            hint="Verify the PID is still running and accessible.",
            command=command,
        )

    if "timeout" in stderr or returncode in (-9, 9, -15, 15):
        return PySpyError(
            error_type="timeout",
            message=f"py-spy {action} timed out or was killed (exit {returncode}).",
            hint="Reduce duration or rate, or ensure the target process is responsive.",
            command=command,
        )

    if "could not find py-spy" in stderr or ("py-spy" in stderr and "not found" in stderr):
        return PySpyError(
            error_type="binary_not_found",
            message=f"py-spy binary not found while {action} (exit {returncode}).",
            hint="Set PYSPY_MCP_BINARY, install py-spy on PATH, or build the Rust workspace.",
            command=command,
        )

    return PySpyError(
        error_type="unknown",
        message=f"py-spy {action} failed (exit {returncode}).",
        hint=stderr[:500] if stderr else "Check stderr for details.",
        command=command,
    )
