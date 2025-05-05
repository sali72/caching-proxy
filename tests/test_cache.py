"""Tests for the ResponseCache class."""

import json
import os
import shutil
from pathlib import Path
from typing import Dict

import pytest

from caching_proxy.cache import ResponseCache


@pytest.fixture
def cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def cache(cache_dir):
    """Create a ResponseCache instance."""
    return ResponseCache(cache_dir)


@pytest.fixture
def sample_response():
    """Create a sample response for testing."""
    return {
        "path": "/test",
        "query": "param=value",
        "method": "GET",
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "content": '{"test": "data"}',
        "cached_at": "2024-01-01T00:00:00"
    }


@pytest.mark.asyncio
async def test_cache_store_and_get(cache, sample_response):
    """Test storing and retrieving from cache."""
    # Store response
    await cache.store(
        method="GET",
        path="/test",
        query_string="param=value",
        request_headers={"Accept": "application/json"},
        status=200,
        response_headers={"Content-Type": "application/json"},
        content=b'{"test": "data"}'
    )

    # Get from cache
    cached = await cache.get(
        method="GET",
        path="/test",
        query_string="param=value",
        headers={"Accept": "application/json"}
    )

    assert cached is not None
    assert cached["path"] == sample_response["path"]
    assert cached["query"] == sample_response["query"]
    assert cached["method"] == sample_response["method"]
    assert cached["status"] == sample_response["status"]
    assert cached["headers"] == sample_response["headers"]
    assert cached["content"] == sample_response["content"]


@pytest.mark.asyncio
async def test_cache_miss(cache):
    """Test cache miss scenario."""
    cached = await cache.get(
        method="GET",
        path="/nonexistent",
        query_string="",
        headers={}
    )
    assert cached is None


@pytest.mark.asyncio
async def test_non_get_requests_not_cached(cache):
    """Test that non-GET requests are not cached."""
    # Try to cache a POST request
    await cache.store(
        method="POST",
        path="/test",
        query_string="",
        request_headers={},
        status=200,
        response_headers={},
        content=b"test"
    )

    # Verify it wasn't cached
    cached = await cache.get(
        method="POST",
        path="/test",
        query_string="",
        headers={}
    )
    assert cached is None


@pytest.mark.asyncio
async def test_error_responses_not_cached(cache):
    """Test that error responses are not cached."""
    # Try to cache a 404 response
    await cache.store(
        method="GET",
        path="/test",
        query_string="",
        request_headers={},
        status=404,
        response_headers={},
        content=b"Not Found"
    )

    # Verify it wasn't cached
    cached = await cache.get(
        method="GET",
        path="/test",
        query_string="",
        headers={}
    )
    assert cached is None


def test_clear_cache(cache, cache_dir):
    """Test clearing the cache."""
    # Create some test files in the cache directory
    test_file = Path(cache_dir) / "test.json"
    test_file.write_text("test")

    # Clear the cache
    cache.clear()

    # Verify the cache directory is empty but exists
    assert Path(cache_dir).exists()
    assert not list(Path(cache_dir).iterdir())


def test_clear_nonexistent_cache(cache, tmp_path):
    """Test clearing a nonexistent cache directory."""
    # Use a nonexistent directory
    cache.cache_dir = tmp_path / "nonexistent"
    
    # Should not raise an exception
    cache.clear()
    
    # Directory should be created
    assert cache.cache_dir.exists()


@pytest.mark.asyncio
async def test_cache_key_generation(cache):
    """Test cache key generation."""
    # Same request should generate same key
    key1 = cache._generate_cache_key(
        method="GET",
        path="/test",
        query_string="param=value",
        headers={"Accept": "application/json"}
    )
    
    key2 = cache._generate_cache_key(
        method="GET",
        path="/test",
        query_string="param=value",
        headers={"Accept": "application/json"}
    )
    
    assert key1 == key2
    
    # Different headers should generate different keys
    key3 = cache._generate_cache_key(
        method="GET",
        path="/test",
        query_string="param=value",
        headers={"Accept": "text/html"}
    )
    
    assert key1 != key3 