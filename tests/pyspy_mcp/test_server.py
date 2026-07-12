from __future__ import annotations

import argparse
import asyncio
import json
from unittest.mock import patch

from pyspy_mcp.server import mcp, parse_args, setup_logging


def test_parse_args_defaults():
    args = parse_args([])
    assert args.transport == "stdio"
    assert args.port == 8080
    assert args.verbose is False


def test_parse_args_verbose():
    args = parse_args(["--verbose"])
    assert args.verbose is True


def test_parse_args_http_port():
    args = parse_args(["--transport", "http", "--port", "9000"])
    assert args.transport == "http"
    assert args.port == 9000


def test_setup_logging_configures_level():
    with patch("logging.basicConfig") as mock_config:
        setup_logging(False)
        assert mock_config.called
        kwargs = mock_config.call_args.kwargs
        assert kwargs["level"] == 20  # logging.INFO


def test_resource_list_processes_registered():
    resources = asyncio.run(mcp.list_resources())
    uris = [str(r.uri) for r in resources]
    assert "python://processes" in uris


def test_resource_list_processes_returns_json():
    result = asyncio.run(mcp.read_resource("python://processes"))
    assert len(result.contents) == 1
    data = json.loads(result.contents[0].content)
    assert isinstance(data, list)


def test_main_runs_stdio_without_port():
    """stdio transport must not pass 'port' to FastMCP.run."""
    from unittest.mock import patch
    from pyspy_mcp import server

    with patch.object(server, "parse_args", return_value=argparse.Namespace(
        verbose=False, transport="stdio", port=8080
    )):
        with patch.object(server.mcp, "run") as mock_run:
            server.main()
    mock_run.assert_called_once()
    kwargs = mock_run.call_args.kwargs
    assert kwargs.get("transport") == "stdio"
    assert "port" not in kwargs
    assert kwargs.get("show_banner") is False


def test_main_runs_http_with_port():
    """http transport must pass port to FastMCP.run."""
    from unittest.mock import patch
    from pyspy_mcp import server

    with patch.object(server, "parse_args", return_value=argparse.Namespace(
        verbose=False, transport="http", port=9000
    )):
        with patch.object(server.mcp, "run") as mock_run:
            server.main()
    kwargs = mock_run.call_args.kwargs
    assert kwargs.get("transport") == "http"
    assert kwargs.get("port") == 9000
    assert kwargs.get("show_banner") is False
