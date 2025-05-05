"""HTTP Caching Proxy Server using aiohttp."""

import logging


import aiohttp
from aiohttp import web
import asyncio

from caching_proxy.cache import ResponseCache

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProxyServer:
    """HTTP proxy server that caches responses."""

    def __init__(self, target_url: str, cache: ResponseCache):
        """
        Initialize the proxy server.

        Args:
            target_url: The URL to proxy requests to
            cache: Response cache instance
        """
        self.target_url = target_url.rstrip("/")
        self.cache = cache

    async def handle_request(self, request: web.Request) -> web.Response:
        """
        Handle an incoming HTTP request.

        Args:
            request: aiohttp request object

        Returns:
            aiohttp response object
        """
        method = request.method
        path = request.path
        query_string = request.query_string
        headers = dict(request.headers)

        # Try to get from cache for GET requests
        cached = await self.cache.get(method, path, query_string, headers)
        if cached:
            logger.info(f"Serving from cache: {method} {path}")
            response = web.Response(
                status=cached["status"],
                headers={**cached["headers"], "X-Cache": "HIT"},
                body=cached["content"].encode("utf-8"),
            )
            return response

        # Forward the request to the target
        target_url = f"{self.target_url}{path}"
        if query_string:
            target_url = f"{target_url}?{query_string}"

        # Remove problematic headers
        for header in ("Host", "Content-Length"):
            headers.pop(header, None)

        try:
            logger.info(f"Forwarding request to {target_url}")

            # Get request body if present
            body = await request.read() if method in ("POST", "PUT", "PATCH") else None

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    data=body,
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as client_response:

                    # Read response content
                    content = await client_response.read()
                    status = client_response.status
                    response_headers = dict(client_response.headers)

                    # Add X-Cache header
                    response_headers["X-Cache"] = "MISS"

                    # Cache successful GET responses
                    if method == "GET" and 200 <= status < 400:
                        await self.cache.store(
                            method,
                            path,
                            query_string,
                            headers,
                            status,
                            response_headers,
                            content,
                        )

                    return web.Response(
                        status=status, headers=response_headers, body=content
                    )

        except asyncio.TimeoutError:
            logger.error(f"Timeout forwarding request to {target_url}")
            return web.Response(
                status=504,
                text="Gateway Timeout: The server timed out waiting for the target URL",
            )
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return web.Response(
                status=502, text=f"Bad Gateway: Error forwarding request: {str(e)}"
            )


async def create_app(target_url: str, cache_dir: str = ".cache") -> web.Application:
    """
    Create the aiohttp web application.

    Args:
        target_url: Target URL to proxy requests to
        cache_dir: Directory to store cached responses

    Returns:
        Configured aiohttp application
    """
    # Create cache and proxy instances
    cache = ResponseCache(cache_dir)
    proxy = ProxyServer(target_url, cache)

    # Create application
    app = web.Application()

    # Add catch-all route for all HTTP methods
    app.router.add_route("*", "/{tail:.*}", proxy.handle_request)

    return app


def run_server(target_url: str, port: int = 8000, cache_dir: str = ".cache") -> None:
    """
    Run the caching proxy server.

    Args:
        target_url: The URL to proxy requests to
        port: Port to run the server on
        cache_dir: Directory to store cached responses
    """
    logger.info(f"Starting caching proxy for {target_url} on port {port}")

    # Create and run the web application
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app(target_url, cache_dir))

    web.run_app(app, host="0.0.0.0", port=port)
