"""Tests for parser edge cases and robustness."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from pyspy_mcp import parser


def test_analyze_speedscope_empty_returns_empty():
    data = {
        "shared": {"frames": []},
        "profiles": [],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        assert parser.analyze_speedscope(path, top_n=10) == []
    finally:
        os.unlink(path)


def test_analyze_speedscope_corrupt_frame_index_is_ignored():
    """A frame index beyond the frames list should be skipped, not crash."""
    data = {
        "shared": {"frames": [{"name": "only", "file": "x.py", "line": 1}]},
        "profiles": [
            {
                "type": "sampled",
                "name": "main",
                "unit": "seconds",
                "startValue": 0.0,
                "endValue": 1.0,
                "samples": [[0, 99]],  # 99 is out of range
                "weights": [1.0],
            }
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        frames = parser.analyze_speedscope(path, top_n=10)
        assert len(frames) == 1
        assert frames[0].name == "only"
    finally:
        os.unlink(path)


def test_analyze_profile_json_fallback_to_raw(tmp_path):
    """If speedscope parsing fails, analyze_profile should fall back to raw parser for .txt."""
    raw = tmp_path / "profile.txt"
    raw.write_text("a (x.py:1);b (x.py:2);c (x.py:3) 5\n")
    result = parser.parse_raw(raw, top_n=5)
    assert len(result) == 1
    assert result[0].name == "c (x.py:3)"


def test_parse_raw_skips_invalid_lines():
    raw_content = """
<module> (x.py:1);foo (x.py:2) 3
malformed line
<module> (x.py:1);bar (x.py:3) 2
no_count_here
<module> (x.py:1);baz (x.py:4) not_a_number
"""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(raw_content)
        path = f.name
    try:
        frames = parser.parse_raw(path, top_n=10)
        names = {f.name for f in frames}
        assert "foo (x.py:2)" in names
        assert "bar (x.py:3)" in names
        assert "baz (x.py:4)" not in names
    finally:
        os.unlink(path)


def test_compare_profiles_same_profile_zero_delta():
    data = {
        "shared": {"frames": [{"name": "foo", "file": "foo.py", "line": 1}]},
        "profiles": [
            {
                "type": "sampled",
                "name": "p",
                "unit": "seconds",
                "startValue": 0.0,
                "endValue": 10.0,
                "samples": [[0]] * 10,
                "weights": [1.0] * 10,
            }
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        result = parser.compare_profiles(path, path, top_n=1)
        assert "foo" in result
        assert "0" in result
    finally:
        os.unlink(path)


def test_parse_dump_json_returns_list():
    dump_data = [
        {
            "pid": 1,
            "thread_id": 1,
            "frames": [{"name": "main", "filename": "main.py", "line": 1}],
        }
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(dump_data, f)
        path = f.name
    try:
        data = parser.parse_dump_json(path)
        assert isinstance(data, list)
        assert data[0]["pid"] == 1
    finally:
        os.unlink(path)
