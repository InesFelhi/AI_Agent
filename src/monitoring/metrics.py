"""
metrics.py
Prometheus metrics for monitoring the server.

Exposes metrics for:
- HTTP requests (total, duration, status codes)
- Active requests
- Server health status
"""

from prometheus_client import Counter, Gauge, Histogram

# Total HTTP requests by method, endpoint, and status
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"]
)

# Current active requests
ACTIVE_REQUESTS = Gauge(
    "active_http_requests",
    "Current number of HTTP requests being processed"
)

# Request duration histogram
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    ["endpoint", "method"]
)

# Server health status (1 = up, 0 = down)
SERVER_UP = Gauge(
    "server_up",
    "1 if server is healthy and responding"
)

# HTTP status codes distribution
HTTP_STATUS_CODE_TOTAL = Counter(
    "http_status_code_total",
    "Total HTTP responses grouped by status code",
    ["http_status"]
)
