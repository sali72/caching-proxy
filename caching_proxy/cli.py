"""Command-line interface for Caching Proxy."""

import sys
import argparse
from typing import List, Optional

from caching_proxy import __version__
from caching_proxy.server import run_server
from caching_proxy.cache import ResponseCache


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
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Run server command
    run_parser = subparsers.add_parser("run", help="Run the proxy server")
    run_parser.add_argument(
        "url",
        help="Target URL to proxy requests to"
    )
    run_parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to run the proxy server on (default: 8000)"
    )
    run_parser.add_argument(
        "-c", "--cache-dir",
        type=str,
        default=".cache",
        help="Directory to store cached responses (default: .cache)"
    )
    run_parser.add_argument(
        "--no-cache",
        type=str,
        nargs="+",
        default=[],
        help="List of path patterns that should not be cached. "
             "Example: --no-cache '/realtime/*' '/api/status'"
    )
    
    # Clear cache command
    clear_parser = subparsers.add_parser("clear-cache", help="Clear the cache")
    clear_parser.add_argument(
        "-c", "--cache-dir",
        type=str,
        default=".cache",
        help="Directory containing cached responses (default: .cache)"
    )
    
    # Add version argument to main parser
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
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
        
        if parsed_args.command == "run":
            target_url = parsed_args.url
            port = parsed_args.port
            cache_dir = parsed_args.cache_dir
            no_cache_paths = parsed_args.no_cache
            
            # Run the proxy server
            run_server(
                target_url=target_url,
                port=port,
                cache_dir=cache_dir,
                no_cache_paths=no_cache_paths
            )
            
        elif parsed_args.command == "clear-cache":
            cache_dir = parsed_args.cache_dir
            cache = ResponseCache(cache_dir)
            cache.clear()
            print("Cache cleared successfully")
            
        else:
            print("No command specified. Use --help for usage information.")
            return 1
            
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Operation stopped", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main()) 