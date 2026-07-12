# py-spy / pyspy-mcp workspace instructions

## Project overview

This workspace now contains two things:

1. `py-spy` Rust source — a sampling profiler for Python programs.
2. `src/pyspy_mcp/` — a Python MCP (Model Context Protocol) server that exposes py-spy based performance testing tools.

The Python package is intended for PyPI distribution. It depends on the published `py-spy` wheel for runtime, but during local development it will automatically use a `py-spy` binary built from the sibling Rust source (`target/release/py-spy`).

## Directory layout

- `src/pyspy/` — Rust source for py-spy.
  - `src/pyspy/python_bindings/vX_Y_Z.rs` — Auto-generated CPython struct bindings. Do not hand-edit.
  - `src/pyspy/lib.rs`, `src/pyspy/main.rs` — Library and CLI entry points.
  - `src/pyspy/python_spy.rs`, `src/pyspy/sampler.rs` — Core profiling/sampling logic.
- `src/pyspy_mcp/` — Python MCP server.
  - `server.py` — FastMCP app and tool definitions.
  - `tools.py` — Wrappers that invoke py-spy and return results.
  - `parser.py` — Parsers for speedscope, raw, and dump JSON output.
  - `process_util.py` — Helper to list running Python processes.
  - `py_spy_finder.py` — Locates the py-spy binary (env var > local build > bundled > PATH).
- `tests/pyspy_mcp/` — Unit and integration tests for the Python MCP server.
- `tests/scripts/` — Python scripts used by the Rust integration tests and MCP integration tests.

## Build, test, and publish

### Rust (py-spy)

```bash
cargo build --release
```

Produces `target/release/py-spy` (Linux/macOS) or `target/release/py-spy.exe` (Windows).

### Python MCP server

```bash
# Editable install (uses PyPI py-spy by default; local target/release build takes precedence if present)
pip install -e ".[dev]"

# Run the server
pyspy-mcp

# Run tests
python -m pytest tests/pyspy_mcp -v
```

If your environment has conflicting pytest plugins (e.g. hydra/omegaconf), run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/pyspy_mcp -v
```

Test file overview:

- `tests/pyspy_mcp/test_integration.py` — end-to-end tests using `record_profile`, `dump_stacks`, and `list_python_processes` against a real Python subprocess.
- `tests/pyspy_mcp/test_integration_top.py` — integration tests for `top_profile` (uses a raw-recording fallback on Windows because `py-spy top` cannot be piped on Windows).
- `tests/pyspy_mcp/test_integration_errors.py` — tests for parameter validation and missing PID/profile errors.
- `tests/pyspy_mcp/test_tools.py` — unit tests for speedscope/raw parsing and aggregation.
- `tests/pyspy_mcp/test_parser_edge_cases.py` — parser robustness tests (empty profiles, corrupt frame indices, invalid raw lines).
- `tests/pyspy_mcp/test_py_spy_finder.py` — tests for binary resolution order and helper logic.
- `tests/pyspy_mcp/test_process_util.py` — tests for Python process detection and listing.

### Publish to PyPI

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

The published wheel is `py3-none-any` and depends on the upstream `py-spy` package. If you modify the Rust source and want to ship those changes in the Python package, build platform-specific wheels that bundle the rebuilt `py-spy` binary.

## Architecture notes

- `src/pyspy_mcp` uses **FastMCP 3.x** and exposes tools over stdio.
- `src/pyspy_mcp/py_spy_finder.py` resolves the py-spy binary in this order:
  1. `PYSPY_MCP_BINARY` environment variable.
  2. The local Rust build at `target/release/py-spy[.exe]` (useful during development).
  3. A binary bundled inside the Python package (`src/pyspy_mcp/bin/`).
  4. `py-spy` found on `PATH` (provided by the PyPI dependency).
- `src/pyspy/python_bindings/*.rs` are generated bindings for CPython versions. If the CPython ABI changes, regenerate them; do not edit by hand.
- Many Rust modules are feature-gated (`cli`, `unwind`) and platform-gated (`target_os`, `target_arch`).

## Platform/permission gotchas

- Profiling an existing PID on Linux usually requires `ptrace` / `CAP_SYS_PTRACE` (use `sudo` or set the capability).
- macOS typically requires root and is blocked by System Integrity Protection (SIP) for system binaries.
- Windows may require Administrator for some processes.
- `--native` (native extension profiling) is only supported on specific platforms; the MCP tools default to `native=False`.
- FreeBSD attach requires `PYSPY_ALLOW_FREEBSD_ATTACH=1`.

## Files to read before changing sensitive areas

- `README.md` — installation, usage, and publishing instructions.
- `src/pyspy_mcp/server.py` — tool schemas and descriptions.
- `src/pyspy_mcp/tools.py` — how py-spy commands are constructed.
- `src/pyspy_mcp/parser.py` — profile output parsing logic.
- `src/pyspy/lib.rs` — public Rust API and feature gates.
- `src/pyspy/config.rs` — CLI option handling and platform restrictions.
