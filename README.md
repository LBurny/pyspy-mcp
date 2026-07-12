# py-spy MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes Python performance testing tools powered by [py-spy](https://github.com/benfred/py-spy).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-2ea44f)
![tests passing](https://img.shields.io/badge/tests-passing-brightgreen)

🌐 English | [简体中文](README.zh.md)

**Profile Python in context.** Sample live processes, generate flamegraphs, dump stacks, and compare runs — all through MCP.

## Features

- **Profile by PID or command** — sample a running Python process or launch a new one directly.
- **`record_profile`** — generate profiles in multiple formats:
  - `speedscope` (interactive JSON)
  - `flamegraph` (self-contained SVG)
  - `raw` (stack-count text)
  - `chrometrace` (Chrome DevTools timeline JSON)
- **`dump_stacks`** — capture the current Python call stacks of a process as JSON or human-readable text.
- **`list_python_processes`** — list running Python processes on the machine to pick a target.
- **`analyze_profile`** — parse an existing profile and return the hottest frames.
- **`compare_profiles`** — compare two speedscope profiles and show percentage changes.
- **`top_profile`** — run a short `py-spy top` session and return a summary.
  - On Windows, `py-spy top` cannot be captured through a pipe, so this tool falls back to a short raw recording and returns the hottest frames.
- **Low-overhead sampling** — powered by [py-spy](https://github.com/benfred/py-spy); reads process memory without modifying or running inside the target process.
- **Cross-platform** — works on Linux, macOS, and Windows (subject to OS permissions).
- **Local-source friendly** — during development the server automatically prefers a `py-spy` binary built from the sibling Rust source (`src/pyspy/`).
- **Optional native/C extension profiling** — enable `--native` where the platform supports it.
- **GIL and idle filtering** — focus on active threads or GIL-holding threads.

## Installation (from PyPI)

Using `pip`:

```bash
pip install pyspy-mcp
```

Using `uv`:

```bash
uv pip install pyspy-mcp
# or install as a global tool
uv tool install pyspy-mcp
```

This will automatically install the compatible `py-spy` binary wheel for your platform.

## Running with Claude Desktop / Claude Code

Add the server as a **Local command** connector:

```json
{
  "mcpServers": {
    "pyspy": {
      "command": "pyspy-mcp"
    }
  }
}
```

Or run directly:

```bash
pyspy-mcp
```

The server speaks MCP over stdio.

## Development (from source)

If you want to use the local py-spy Rust source instead of the PyPI package:

```bash
# Build py-spy from the local Rust source
cargo build --release

# The binary will be at:
#   target/release/py-spy        (Linux / macOS)
#   target/release/py-spy.exe    (Windows)

# Install the Python MCP package in editable mode
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"

# Run tests
python -m pytest tests/pyspy_mcp -v
```

The server will automatically prefer a locally built binary at `target/release/py-spy[.exe]` over the `py-spy` installed from PyPI. You can also force a specific binary by setting the environment variable:

```bash
export PYSPY_MCP_BINARY=/path/to/py-spy
```

## Publishing to PyPI

```bash
python -m build
python -m twine upload dist/*
```

The published wheel is a pure-Python `py3-none-any` package and depends on the upstream `py-spy` PyPI package. If you modify the Rust source and want to ship those changes, you will need to build platform-specific wheels (or bundle the rebuilt `py-spy` binary as package data).

## Permissions

- On Linux, profiling an existing PID usually requires `ptrace` permissions (`sudo` or `cap_sys_ptrace`).
- On macOS, profiling often requires root due to System Integrity Protection (SIP).
- On Windows, running as Administrator may be needed for some processes.

## Configuration

Set `PYSPY_MCP_BINARY` to override the bundled/development py-spy binary location.
