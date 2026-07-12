# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-12

### Added

- New `pyspy_mcp.errors` module that maps `py-spy` subprocess failures to structured error responses (`permission_denied`, `process_not_found`, `timeout`, `binary_not_found`, `unknown`). Each error includes a machine-readable `error_type`, a `message`, and an actionable `hint`.
- New `pyspy_mcp.cleanup` module with `temp_file` and `managed_subprocess` context managers for guaranteed cleanup of temporary files and subprocesses.
- CLI arguments for the `pyspy-mcp` entry point: `--version`, `--verbose`, `--transport {stdio,http}`, and `--port`.
- Startup logging that reports the server version and the resolved `py-spy` binary path.
- New MCP resource `python://processes` that returns a JSON list of currently running Python processes.
- Tests covering the error module, cleanup helpers, server CLI/resource configuration, and tool cleanup paths.

### Changed

- `tools.py` now uses structured errors instead of generic `RuntimeError` exceptions, while remaining backward-compatible with callers that catch `RuntimeError`.
- `record_profile` and the Windows fallback in `top_profile` now automatically remove temporary files.
- `top_profile` now uses `managed_subprocess` to ensure the `py-spy top` process is always terminated, and inline imports have been moved to module level.
- `mcp.run()` no longer passes the `port` argument when the stdio transport is used.

### Fixed

- Fixed `TypeError: TransportMixin.run_stdio_async() got an unexpected keyword argument 'port'` when running `pyspy-mcp` as a stdio MCP server.
- Disabled the FastMCP startup banner to keep `stderr` clean for MCP clients.

## [0.1.0] - 2026-07-12

### Added

- Initial release of `pyspy-mcp`.
- MCP tools powered by `py-spy`: `record_profile`, `dump_stacks`, `list_python_processes`, `analyze_profile`, `compare_profiles`, and `top_profile`.
- Support for profiling by PID or command with multiple output formats (`speedscope`, `flamegraph`, `raw`, `chrometrace`).
- Automatic resolution of the `py-spy` binary via `PYSPY_MCP_BINARY`, local Rust build, bundled binary, or PATH.

[Unreleased]: https://github.com/LBurny/pyspy-mcp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/LBurny/pyspy-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LBurny/pyspy-mcp/releases/tag/v0.1.0
