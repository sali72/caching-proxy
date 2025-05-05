"""Command-line interface for Caching Proxy."""

import sys
import argparse
from typing import List, Optional

from caching_proxy import __version__
from caching_proxy.server import run_server


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: List of command-line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="caching-proxy",
        description="Cache HTTP requests and serve from cache when possible."
    )
    
    parser.add_argument(
        "url",
        help="Target URL to proxy requests to"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to run the proxy server on (default: 8000)"
    )
    
    parser.add_argument(
        "-c", "--cache-dir",
        type=str,
        default=".cache",
        help="Directory to store cached responses (default: .cache)"
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: List of command-line arguments
        
    Returns:
        Exit code
    """
    try:
        parsed_args = parse_args(args)
        target_url = parsed_args.url
        port = parsed_args.port
        cache_dir = parsed_args.cache_dir
        
        # Run the proxy server
        run_server(target_url=target_url, port=port, cache_dir=cache_dir)
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Proxy server stopped", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main()) 