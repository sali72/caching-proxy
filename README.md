# 🚀 Caching Proxy

A HTTP caching proxy server that helps reduce load on origin servers and improve response times for clients.

## ✨ Features

- 🔄 HTTP/HTTPS request proxying
- 💾 Response caching for improved performance
- 🎯 Path-based cache control
- 📊 Cache hit/miss headers
- ⚡ Async/await based implementation
- 🔒 Secure header handling
- 📝 Detailed logging

## 🛠️ Installation

```bash
pip install caching-proxy
```

## 🚀 Quick Start

Start the proxy server with default settings:

```bash
caching-proxy http://example.com
```

## ⚙️ Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p, --port` | Port to run the proxy server on | `8000` |
| `-c, --cache-dir` | Directory to store cached responses | `.cache` |
| `--no-cache` | Path patterns that should not be cached | `[]` |

## 📋 Usage Examples

### Basic Usage
```bash
caching-proxy http://example.com
```

### Custom Port and Cache Directory
```bash
caching-proxy http://example.com --port 8080 --cache-dir .mycache
```

### Exclude Paths from Caching
```bash
caching-proxy http://example.com --no-cache "/realtime/*" "/api/status" "/live/*"
```

## 🔍 How It Works

1. **Request Handling**:
   - Receives HTTP requests from clients
   - Checks if the path should be cached
   - Forwards requests to the origin server if needed

2. **Caching Logic**:
   - Caches successful GET responses (status 200-399)
   - Adds `X-Cache: HIT` for cached responses
   - Adds `X-Cache: MISS` for origin server responses

3. **Path-based Control**:
   - Uses regular expressions for path matching
   - Allows fine-grained control over which paths are cached
   - Supports wildcards and pattern matching

## 🛡️ Security Considerations

- Removes sensitive headers before forwarding requests
- Handles timeouts and errors gracefully
- Provides detailed error messages for debugging

## 📝 Logging

The proxy server provides detailed logging including:
- Request forwarding
- Cache hits/misses
- Error conditions
- Server startup/shutdown

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
