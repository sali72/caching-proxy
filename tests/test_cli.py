"""Tests for the CLI interface."""

import sys
from unittest.mock import patch

import pytest

from caching_proxy.cli import main, parse_args


def test_parse_args_run():
    """Test parsing run command arguments."""
    args = parse_args(["run", "http://example.com"])
    assert args.command == "run"
    assert args.url == "http://example.com"
    assert args.port == 8000
    assert args.cache_dir == ".cache"
    assert args.no_cache == []


def test_parse_args_run_with_options():
    """Test parsing run command with options."""
    args = parse_args([
        "run",
        "http://example.com",
        "--port", "8080",
        "--cache-dir", ".mycache",
        "--no-cache", "/realtime/*", "/api/status"
    ])
    assert args.command == "run"
    assert args.url == "http://example.com"
    assert args.port == 8080
    assert args.cache_dir == ".mycache"
    assert args.no_cache == ["/realtime/*", "/api/status"]


def test_parse_args_clear_cache():
    """Test parsing clear-cache command."""
    args = parse_args(["clear-cache"])
    assert args.command == "clear-cache"
    assert args.cache_dir == ".cache"


def test_parse_args_clear_cache_with_options():
    """Test parsing clear-cache command with options."""
    args = parse_args(["clear-cache", "--cache-dir", ".mycache"])
    assert args.command == "clear-cache"
    assert args.cache_dir == ".mycache"


def test_parse_args_version():
    """Test version argument."""
    with pytest.raises(SystemExit):
        parse_args(["--version"])


def test_parse_args_no_command():
    """Test parsing with no command."""
    args = parse_args([])
    assert args.command is None


@patch("caching_proxy.cli.run_server")
def test_main_run(mock_run_server):
    """Test main function with run command."""
    sys.argv = ["caching-proxy", "run", "http://example.com"]
    assert main() == 0
    mock_run_server.assert_called_once_with(
        target_url="http://example.com",
        port=8000,
        cache_dir=".cache",
        no_cache_paths=[]
    )


@patch("caching_proxy.cli.ResponseCache")
def test_main_clear_cache(mock_cache):
    """Test main function with clear-cache command."""
    sys.argv = ["caching-proxy", "clear-cache"]
    assert main() == 0
    mock_cache.assert_called_once_with(".cache")
    mock_cache.return_value.clear.assert_called_once()


def test_main_no_command():
    """Test main function with no command."""
    sys.argv = ["caching-proxy"]
    assert main() == 1


@patch("caching_proxy.cli.run_server")
def test_main_keyboard_interrupt(mock_run_server):
    """Test handling keyboard interrupt."""
    mock_run_server.side_effect = KeyboardInterrupt()
    sys.argv = ["caching-proxy", "run", "http://example.com"]
    assert main() == 0


@patch("caching_proxy.cli.run_server")
def test_main_error(mock_run_server):
    """Test handling errors."""
    mock_run_server.side_effect = Exception("Test error")
    sys.argv = ["caching-proxy", "run", "http://example.com"]
    assert main() == 2 