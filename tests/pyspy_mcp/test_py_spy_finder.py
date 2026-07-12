"""Tests for py-spy binary resolution logic."""

from __future__ import annotations

import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from pyspy_mcp import py_spy_finder


class TestFindPySpy:
    """End-to-end resolution tests with temporary files."""

    def test_env_variable_wins(self, monkeypatch):
        """PYSPY_MCP_BINARY is used when set and exists."""
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("")
            env_path = f.name
        monkeypatch.setenv("PYSPY_MCP_BINARY", env_path)
        try:
            assert py_spy_finder.find_py_spy() == env_path
        finally:
            os.unlink(env_path)

    def test_env_variable_missing_raises(self, monkeypatch):
        """A missing PYSPY_MCP_BINARY raises FileNotFoundError."""
        monkeypatch.setenv("PYSPY_MCP_BINARY", "/non/existent/py-spy")
        with pytest.raises(FileNotFoundError):
            py_spy_finder.find_py_spy()

    def test_path_lookup(self, monkeypatch, tmp_path):
        """A py-spy binary on PATH is found."""
        name = "py-spy.exe" if sys.platform == "win32" else "py-spy"
        binary = tmp_path / name
        binary.write_text("")
        monkeypatch.setenv("PATH", str(tmp_path), prepend=os.pathsep)
        monkeypatch.delenv("PYSPY_MCP_BINARY", raising=False)
        found = py_spy_finder.find_py_spy()
        assert Path(found).name.lower().startswith("py-spy")

    def test_missing_everything_raises(self, monkeypatch):
        """When nothing is available, find_py_spy raises FileNotFoundError."""
        monkeypatch.delenv("PYSPY_MCP_BINARY", raising=False)
        with mock.patch.object(shutil, "which", return_value=None):
            with mock.patch.object(py_spy_finder, "_bundled_binary", return_value=None):
                with mock.patch.object(py_spy_finder, "_development_binary", return_value=None):
                    with pytest.raises(FileNotFoundError):
                        py_spy_finder.find_py_spy()


class TestBinaryHelpers:
    """Unit tests for helper functions in py_spy_finder."""

    def test_bundled_binary_found(self, tmp_path, monkeypatch):
        """A binary inside the package bin dir is detected."""
        package_dir = tmp_path / "pyspy_mcp"
        bin_dir = package_dir / "bin"
        bin_dir.mkdir(parents=True)
        name = "py-spy.exe" if sys.platform == "win32" else "py-spy"
        binary = bin_dir / name
        binary.write_text("")

        def fake_bundled():
            candidate = bin_dir / py_spy_finder._binary_name()
            return candidate if candidate.exists() else None

        monkeypatch.setattr(py_spy_finder, "_bundled_binary", fake_bundled)
        assert py_spy_finder._bundled_binary() == bin_dir / name

    def test_development_binary_found(self, tmp_path, monkeypatch):
        """A binary in target/release relative to the package is detected."""
        workspace = tmp_path / "workspace"
        target = workspace / "target" / "release"
        target.mkdir(parents=True)
        name = "py-spy.exe" if sys.platform == "win32" else "py-spy"
        binary = target / name
        binary.write_text("")

        monkeypatch.setattr(
            py_spy_finder,
            "__file__",
            str(workspace / "src" / "pyspy_mcp" / "py_spy_finder.py"),
        )
        result = py_spy_finder._development_binary()
        assert result == binary

    def test_binary_name_on_windows(self):
        """_binary_name returns py-spy.exe on Windows."""
        with mock.patch.object(platform, "system", return_value="Windows"):
            assert py_spy_finder._binary_name() == "py-spy.exe"

    def test_binary_name_on_unix(self):
        """_binary_name returns py-spy on non-Windows."""
        for system in ("Linux", "Darwin", "FreeBSD"):
            with mock.patch.object(platform, "system", return_value=system):
                assert py_spy_finder._binary_name() == "py-spy"
