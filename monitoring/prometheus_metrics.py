import time
from typing import Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


QUERY_TOTAL = Counter(
    "llmops_queries_total",
    "Total number of queries processed, by agent route",
    ["route"],
)

QUERY_LATENCY = Histogram(
    "llmops_query_latency_seconds",
    "Query latency in seconds, by agent route",
    ["route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

QUERY_VALID = Counter(
    "llmops_queries_valid_total",
    "Number of queries that passed validation",
)

QUERY_INVALID = Counter(
    "llmops_queries_invalid_total",
    "Number of queries that failed validation",
)

ERROR_TOTAL = Counter(
    "llmops_errors_total",
    "Errors recorded, by component and error type",
    ["component", "error_type"],
)

TOKENS_TOTAL = Counter(
    "llmops_tokens_total",
    "Total number of LLM tokens consumed",
)

TOKENS_MEAN = Gauge(
    "llmops_tokens_mean",
    "Mean tokens consumed per query (rolling window)",
)

SUCCESS_RATE = Gauge(
    "llmops_success_rate_percent",
    "Percentage of queries that passed validation (rolling window)",
)

UPTIME_SECONDS = Gauge(
    "llmops_uptime_seconds",
    "Seconds since the metrics collector was started",
)

ACTIVE_AGENTS = Gauge(
    "llmops_active_agents",
    "Number of distinct agent routes observed",
)

CUSTOM_METRICS = Gauge(
    "llmops_custom_metric",
    "Custom application metric",
    ["metric_name"],
)

HTTP_REQUESTS = Counter(
    "llmops_http_requests_total",
    "HTTP requests served, by method, path and status",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "llmops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, float("inf")),
)

HTTP_INFLIGHT = Gauge(
    "llmops_http_requests_inflight",
    "HTTP requests currently being processed",
)


def record_query(
    route: str,
    latency_ms: float,
    is_valid: bool = True,
    token_count: Optional[int] = None,
) -> None:
    route = route or "UNKNOWN"
    QUERY_TOTAL.labels(route=route).inc()
    QUERY_LATENCY.labels(route=route).observe(latency_ms / 1000.0)
    if is_valid:
        QUERY_VALID.inc()
    else:
        QUERY_INVALID.inc()
    if token_count:
        TOKENS_TOTAL.inc(token_count)


def record_error(error_type: str, component: str) -> None:
    ERROR_TOTAL.labels(component=component, error_type=error_type).inc()


def record_custom(metric_name: str, value: float) -> None:
    CUSTOM_METRICS.labels(metric_name=metric_name).set(value)


def sync_from_summary(summary: dict) -> None:
    """Sync rolling-window aggregates from the in-memory MetricsCollector."""
    try:
        SUCCESS_RATE.set(summary.get("success_rate", 100.0))
        UPTIME_SECONDS.set(summary.get("uptime_seconds", 0.0))

        latency = summary.get("latency", {})
        if latency.get("mean"):
            QUERY_LATENCY._sum += latency.get("mean", 0.0) / 1000.0 * latency.get("count", 0)
            QUERY_LATENCY._count += latency.get("count", 0)

        tokens = summary.get("tokens", {})
        if tokens.get("mean"):
            TOKENS_MEAN.set(tokens.get("mean", 0.0))

        agents = summary.get("agent_performance", {})
        ACTIVE_AGENTS.set(len(agents))
    except Exception:
        pass


class PrometheusMiddleware:
    """ASGI middleware recording HTTP request metrics in Prometheus format."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")

        if path in ("/prometheus/metrics", "/metrics"):
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def wrapped_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        HTTP_INFLIGHT.inc()
        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            HTTP_INFLIGHT.dec()
            duration = time.perf_counter() - start
            HTTP_REQUESTS.labels(method=method, path=path, status=str(status_code)).inc()
            HTTP_REQUEST_DURATION.labels(method=method, path=path).observe(duration)


def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST
