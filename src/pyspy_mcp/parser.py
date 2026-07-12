"""Parsers for py-spy output formats."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class HotFrame:
    name: str
    file: str | None
    line: int | None
    samples: int
    percent: float


def parse_speedscope(profile_path: str | Path) -> Dict:
    """Load a speedscope JSON file and return the raw dict."""
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_speedscope(profile_path: str | Path, top_n: int = 10) -> List[HotFrame]:
    """Aggregate a speedscope profile into the most frequently sampled frames."""
    data = parse_speedscope(profile_path)
    frames = data.get("shared", {}).get("frames", [])
    counts: Counter[int] = Counter()
    total = 0
    for profile in data.get("profiles", []):
        for sample in profile.get("samples", []):
            # Deduplicate frames within a single sample to avoid overweighting deep stacks.
            seen = set()
            for frame_idx in sample:
                if frame_idx not in seen:
                    counts[frame_idx] += 1
                    seen.add(frame_idx)
            total += len(sample)

    if total == 0:
        return []

    hot = []
    for idx, sample_count in counts.most_common(top_n):
        if idx < 0 or idx >= len(frames):
            continue
        frame = frames[idx]
        hot.append(
            HotFrame(
                name=frame.get("name", "<unknown>"),
                file=frame.get("file"),
                line=frame.get("line"),
                samples=sample_count,
                percent=round(100.0 * sample_count / total, 2),
            )
        )
    return hot


def parse_raw(profile_path: str | Path, top_n: int = 10) -> List[HotFrame]:
    """Parse py-spy raw output (semicolon-delimited stacks with counts)."""
    counts: Counter[str] = Counter()
    total = 0
    with open(profile_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ";" not in line:
                continue
            # py-spy raw format: frame1 (file:line);frame2 (file:line) count
            try:
                stack_str, count_str = line.rsplit(" ", 1)
                count = int(count_str)
            except ValueError:
                continue
            counts[stack_str] += count
            total += count

    if total == 0:
        return []

    hot = []
    for stack, sample_count in counts.most_common(top_n):
        # Use the innermost (last) frame as the representative name.
        top_frame = stack.split(";")[-1]
        hot.append(
            HotFrame(
                name=top_frame,
                file=None,
                line=None,
                samples=sample_count,
                percent=round(100.0 * sample_count / total, 2),
            )
        )
    return hot


def parse_dump_json(dump_path: str | Path) -> List[Dict]:
    """Load the output of ``py-spy dump --json``."""
    with open(dump_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_hot_frames(frames: List[HotFrame]) -> str:
    """Render a list of hot frames as a Markdown table."""
    lines = ["| Function | File | Line | Samples | % |", "|---|---|---|---|---|"]
    for f in frames:
        file_cell = f.file or "-"
        line_cell = str(f.line) if f.line is not None else "-"
        lines.append(f"| {f.name} | {file_cell} | {line_cell} | {f.samples} | {f.percent} |")
    return "\n".join(lines)


def _frame_signature(frame: Dict) -> str:
    """Canonical string for a frame used when comparing profiles."""
    return f"{frame.get('name')}@{frame.get('filename')}:{frame.get('line', 0)}"


def compare_profiles(
    profile_a: str | Path,
    profile_b: str | Path,
    top_n: int = 10,
) -> str:
    """Compare two speedscope profiles and highlight changes."""
    frames_a = {f.name: f for f in analyze_speedscope(profile_a, top_n=top_n * 2)}
    frames_b = {f.name: f for f in analyze_speedscope(profile_b, top_n=top_n * 2)}
    all_names = set(frames_a.keys()) | set(frames_b.keys())

    rows = []
    names = sorted(
        all_names,
        key=lambda n: -(frames_b.get(n, HotFrame(n, None, None, 0, 0.0)).percent),
    )
    for name in names[:top_n]:
        a = frames_a.get(name)
        b = frames_b.get(name)
        pct_a = a.percent if a else 0.0
        pct_b = b.percent if b else 0.0
        delta = round(pct_b - pct_a, 2)
        rows.append((name, pct_a, pct_b, delta))

    lines = ["| Function | % in A | % in B | Δ |", "|---|---|---|---|"]
    for name, pct_a, pct_b, delta in rows:
        lines.append(f"| {name} | {pct_a} | {pct_b} | {delta:+} |")
    return "\n".join(lines)
