"""Tests for the ProxyServer class and server functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import web

from caching_proxy.server import ProxyServer, create_app, run_server
from caching_proxy.cache import ResponseCache


@pytest.fixture
def cache():
    """Create a mock cache."""
    return AsyncMock(spec=ResponseCache)


@pytest.fixture
def proxy_server(cache):
    """Create a ProxyServer instance."""
    return ProxyServer("http://example.com", cache)


@pytest.fixture
def mock_request():
    """Create a mock aiohttp request."""
    request = MagicMock(spec=web.Request)
    request.method = "GET"
    request.path = "/test"
    request.query_string = ""
    request.headers = {"Accept": "application/json"}
    request.read = AsyncMock(return_value=b"")
    return request


@pytest.mark.asyncio
async def test_handle_request_cache_hit(proxy_server, mock_request, cache):
    """Test handling a request that hits the cache."""
    # Setup cache hit
    cache.get.return_value = {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "content": "test"
    }

    # Handle request
    response = await proxy_server.handle_request(mock_request)

    # Verify response
    assert response.status == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["X-Cache"] == "HIT"
    assert response.body == b"test"

    # Verify cache was checked
    cache.get.assert_called_once_with(
        "GET", "/test", "", {"Accept": "application/json"}
    )


@pytest.mark.asyncio
async def test_handle_request_cache_miss(proxy_server, mock_request, cache):
    """Test handling a request that misses the cache."""
    # Setup cache miss
    cache.get.return_value = None

    # Mock client session and response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.read = AsyncMock(return_value=b"test")
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    mock_session = AsyncMock()
    mock_session.request.return_value = mock_response
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Mock the nested context manager
    mock_session.request.return_value.__aenter__.return_value = mock_response

    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Handle request
        response = await proxy_server.handle_request(mock_request)

        # Verify response
        assert response.status == 200
        assert response.headers["X-Cache"] == "MISS"
        assert response.headers["Content-Type"] == "application/json"
        assert response.body == b"test"

        # Verify cache was updated
        cache.store.assert_called_once()


@pytest.mark.asyncio
async def test_handle_request_error(proxy_server, mock_request, cache):
    """Test handling a request that results in an error."""
    # Setup cache miss
    cache.get.return_value = None

    # Mock client session to raise an exception
    mock_session = AsyncMock()
    mock_session.request.side_effect = Exception("Test error")
    mock_session.__aenter__.return_value = mock_session

    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Handle request
        response = await proxy_server.handle_request(mock_request)

        # Verify error response
        assert response.status == 502
        assert b"Bad Gateway" in response.body


@pytest.mark.asyncio
async def test_handle_request_timeout(proxy_server, mock_request, cache):
    """Test handling a request that times out."""
    # Setup cache miss
    cache.get.return_value = None

    # Mock client session to raise a timeout
    mock_session = AsyncMock()
    mock_session.request.side_effect = asyncio.TimeoutError()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Handle request
        response = await proxy_server.handle_request(mock_request)

        # Verify timeout response
        assert response.status == 504
        assert b"Gateway Timeout" in response.body


@pytest.mark.asyncio
async def test_should_cache_path():
    """Test path-based cache control."""
    # Create server with no-cache paths
    cache = AsyncMock()
    server = ProxyServer("http://example.com", cache, no_cache_paths=["/realtime/*", "/api/status"])

    # Test paths that should be cached
    assert server.should_cache_path("/test") is True
    assert server.should_cache_path("/api/test") is True

    # Test paths that should not be cached
    assert server.should_cache_path("/realtime/data") is False
    assert server.should_cache_path("/api/status") is False


@pytest.mark.asyncio
async def test_create_app():
    """Test application creation."""
    app = await create_app("http://example.com", ".cache", ["/realtime/*"])
    assert isinstance(app, web.Application)
    assert len(app.router.routes()) == 1  # Should have one catch-all route


def test_run_server():
    """Test server startup."""
    with patch("aiohttp.web.run_app") as mock_run_app:
        run_server("http://example.com", 8000, ".cache", ["/realtime/*"])
        mock_run_app.assert_called_once() 