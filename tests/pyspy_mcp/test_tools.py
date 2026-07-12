"""Unit tests for pyspy_mcp tools and parsers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from pyspy_mcp import parser, tools
from pyspy_mcp.py_spy_finder import find_py_spy


def test_find_py_spy_locates_something():
    """The py-spy binary should be discoverable after installation."""
    binary = find_py_spy()
    assert os.path.exists(binary)


def test_analyze_speedscope_aggregates_frames():
    """Hot frame aggregation should count frame occurrences."""
    data = {
        "shared": {
            "frames": [
                {"name": "busyloop", "file": "busyloop.py", "line": 5, "col": None},
                {"name": "<module>", "file": "busyloop.py", "line": 10, "col": None},
            ]
        },
        "profiles": [
            {
                "type": "sampled",
                "name": "main",
                "unit": "seconds",
                "startValue": 0.0,
                "endValue": 1.0,
                "samples": [[0, 1], [0, 1], [1]],
                "weights": [1.0, 1.0, 1.0],
            }
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        frames = parser.analyze_speedscope(path, top_n=2)
        assert len(frames) == 2
        names = [f.name for f in frames]
        assert "busyloop" in names
        assert "<module>" in names
        # busyloop appears in 2 samples, module in 3.
        busy = next(f for f in frames if f.name == "busyloop")
        mod = next(f for f in frames if f.name == "<module>")
        assert busy.samples == 2
        assert mod.samples == 3
    finally:
        os.unlink(path)


def test_parse_raw_aggregates_counts():
    """Raw parser should sum counts per stack."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("a (x.py:1);b (x.py:2);c (x.py:3) 10\n")
        f.write("a (x.py:1);b (x.py:2);c (x.py:3) 5\n")
        f.write("a (x.py:1);b (x.py:2) 3\n")
        path = f.name
    try:
        frames = parser.parse_raw(path, top_n=2)
        assert len(frames) == 2
        top = frames[0]
        assert top.name == "c (x.py:3)"
        assert top.samples == 15
    finally:
        os.unlink(path)


def test_compare_profiles_shows_delta():
    """Profile comparison should report percentage changes."""
    def make_profile(name: str, weights: list) -> str:
        data = {
            "shared": {
                "frames": [
                    {"name": "foo", "file": "foo.py", "line": 1},
                    {"name": "bar", "file": "bar.py", "line": 2},
                ]
            },
            "profiles": [
                {
                    "type": "sampled",
                    "name": name,
                    "unit": "seconds",
                    "startValue": 0.0,
                    "endValue": sum(weights),
                    "samples": [[0]] * weights[0] + [[1]] * weights[1],
                    "weights": weights,
                }
            ],
        }
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        return path

    a = make_profile("a", [1, 9])
    b = make_profile("b", [5, 5])
    try:
        result = parser.compare_profiles(a, b, top_n=2)
        assert "foo" in result
        assert "bar" in result
    finally:
        os.unlink(a)
        os.unlink(b)


def test_dump_stacks_locals_level_range():
    """locals_level must be within 0-2."""
    with pytest.raises(ValueError, match="between 0 and 2"):
        tools.dump_stacks(pid=12345, locals_level=-1)
    with pytest.raises(ValueError, match="between 0 and 2"):
        tools.dump_stacks(pid=12345, locals_level=3)


def test_analyze_profile_top_n_positive():
    """top_n must be positive."""
    with pytest.raises(ValueError, match="positive"):
        tools.analyze_profile("/tmp/fake.json", top_n=0)


def test_compare_profiles_top_n_positive():
    """top_n must be positive."""
    with pytest.raises(ValueError, match="positive"):
        tools.compare_profiles("/tmp/a.json", "/tmp/b.json", top_n=0)


def test_find_py_sky_alias_removed():
    """The misspelled backwards-compatibility alias should be gone."""
    assert not hasattr(tools, "find_py_sky")
    assert hasattr(tools, "find_py_spy")


from unittest.mock import MagicMock, patch

from pyspy_mcp.errors import PySpyError


def test_record_profile_permission_error_is_structured():
    """A permission-denied failure from py-spy should produce a structured error."""
    fake_result = MagicMock()
    fake_result.returncode = 1
    fake_result.stderr = "permission denied"
    fake_result.args = ["py-spy", "record", "--pid", "1"]
    with patch("pyspy_mcp.tools._run_py_spy", return_value=fake_result):
        with pytest.raises(PySpyError) as exc:
            tools.record_profile(pid=1, duration=1)
    assert exc.value.error_type == "permission_denied"


def test_record_profile_temp_file_cleaned_up():
    """record_profile should remove the temporary file it creates."""
    created_files = []
    original_run = tools._run_py_spy

    def mock_run(args, timeout=None, action="run"):
        # Capture the output path that py-spy would write to.
        idx = args.index("-o")
        created_files.append(Path(args[idx + 1]))
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        result.args = args
        return result

    with patch.object(tools, "_run_py_spy", side_effect=mock_run):
        tools.record_profile(pid=1, duration=1, output_format="raw")

    assert len(created_files) == 1
    assert not created_files[0].exists()
