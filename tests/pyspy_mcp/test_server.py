from __future__ import annotations

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
