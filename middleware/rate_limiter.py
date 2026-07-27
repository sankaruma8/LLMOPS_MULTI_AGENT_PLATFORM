import time
import hashlib
from typing import Optional
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitBucket:

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def consume(self) -> bool:

        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True

        return False

    def get_wait_time(self) -> float:

        if self.tokens >= 1:
            return 0

        return (1 - self.tokens) / self.refill_rate


class RateLimiter:

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        cleanup_interval: int = 300
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.cleanup_interval = cleanup_interval

        self.minute_buckets: dict[str, RateLimitBucket] = {}
        self.hour_buckets: dict[str, RateLimitBucket] = {}
        self.last_cleanup = time.time()

        self.endpoint_limits = {
            "/chat": {"minute": 30, "hour": 500},
            "/chat/stream": {"minute": 30, "hour": 500},
            "/upload": {"minute": 10, "hour": 100},
            "/upload/batch": {"minute": 5, "hour": 50},
        }

    def _get_client_id(self, request: Request) -> str:

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        user_agent = request.headers.get("user-agent", "")
        return hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()

    def _get_bucket_key(self, client_id: str, endpoint: str) -> str:
        return f"{client_id}:{endpoint}"

    def _cleanup_old_buckets(self):

        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = now

        expired = [
            key for key, bucket in self.minute_buckets.items()
            if now - bucket.last_refill > 60
        ]
        for key in expired:
            del self.minute_buckets[key]

        expired = [
            key for key, bucket in self.hour_buckets.items()
            if now - bucket.last_refill > 3600
        ]
        for key in expired:
            del self.hour_buckets[key]

    def check_rate_limit(self, request: Request) -> dict:

        self._cleanup_old_buckets()

        client_id = self._get_client_id(request)
        endpoint = request.url.path

        limits = self.endpoint_limits.get(endpoint, {
            "minute": self.requests_per_minute,
            "hour": self.requests_per_hour
        })

        minute_key = self._get_bucket_key(client_id, f"{endpoint}:minute")
        hour_key = self._get_bucket_key(client_id, f"{endpoint}:hour")

        if minute_key not in self.minute_buckets:
            self.minute_buckets[minute_key] = RateLimitBucket(
                capacity=limits["minute"],
                refill_rate=limits["minute"] / 60
            )

        if hour_key not in self.hour_buckets:
            self.hour_buckets[hour_key] = RateLimitBucket(
                capacity=limits["hour"],
                refill_rate=limits["hour"] / 3600
            )

        minute_bucket = self.minute_buckets[minute_key]
        hour_bucket = self.hour_buckets[hour_key]

        if not minute_bucket.consume():
            wait_time = minute_bucket.get_wait_time()
            return {
                "allowed": False,
                "retry_after": int(wait_time) + 1,
                "limit": limits["minute"],
                "remaining": 0,
                "reset": int(time.time() + wait_time),
                "window": "minute"
            }

        if not hour_bucket.consume():
            wait_time = hour_bucket.get_wait_time()
            return {
                "allowed": False,
                "retry_after": int(wait_time) + 1,
                "limit": limits["hour"],
                "remaining": 0,
                "reset": int(time.time() + wait_time),
                "window": "hour"
            }

        return {
            "allowed": True,
            "limit": limits["minute"],
            "remaining": int(minute_bucket.tokens),
            "reset": int(time.time() + 60),
            "window": "minute"
        }

    def get_stats(self) -> dict:

        return {
            "total_minute_buckets": len(self.minute_buckets),
            "total_hour_buckets": len(self.hour_buckets),
            "endpoint_limits": self.endpoint_limits,
            "default_limits": {
                "per_minute": self.requests_per_minute,
                "per_hour": self.requests_per_hour
            }
        }


rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10
)


class RateLimitMiddleware(BaseHTTPMiddleware):

    SKIP_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):

        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        if request.url.path.startswith("/cache"):
            return await call_next(request)

        rate_limit_result = rate_limiter.check_rate_limit(request)

        if not rate_limit_result["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {rate_limit_result['retry_after']} seconds.",
                    "retry_after": rate_limit_result["retry_after"],
                    "limit": rate_limit_result["limit"],
                    "window": rate_limit_result["window"]
                },
                headers={
                    "Retry-After": str(rate_limit_result["retry_after"]),
                    "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_limit_result["reset"])
                }
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset"])

        return response
