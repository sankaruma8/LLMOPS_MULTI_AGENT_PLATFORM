import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class MetricsCollector:

    def __init__(self, window_size: int = 1000):

        self.window_size = window_size
        self._lock = threading.Lock()

        self._latencies = deque(maxlen=window_size)
        self._agent_latencies = defaultdict(lambda: deque(maxlen=window_size))
        self._route_counts = defaultdict(int)
        self._error_counts = defaultdict(int)
        self._query_count = 0
        self._valid_count = 0
        self._token_counts = deque(maxlen=window_size)

        self._start_time = time.time()

        self._custom_metrics = defaultdict(list)

    def record_query(
        self,
        route: str,
        latency_ms: float,
        is_valid: bool = True,
        token_count: Optional[int] = None,
        agent_name: Optional[str] = None
    ):

        with self._lock:
            self._query_count += 1
            self._latencies.append(latency_ms)

            if is_valid:
                self._valid_count += 1

            self._route_counts[route] += 1

            if token_count:
                self._token_counts.append(token_count)

            if agent_name:
                self._agent_latencies[agent_name].append(latency_ms)

    def record_error(self, error_type: str, component: str):

        with self._lock:
            self._error_counts[f"{component}:{error_type}"] += 1

    def record_custom(self, metric_name: str, value: float):

        with self._lock:
            self._custom_metrics[metric_name].append(value)

    def _calculate_percentile(self, data: deque, percentile: float) -> float:

        if not data:
            return 0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def get_latency_stats(self) -> Dict:

        with self._lock:
            if not self._latencies:
                return {
                    "count": 0,
                    "mean": 0,
                    "min": 0,
                    "max": 0,
                    "p50": 0,
                    "p95": 0,
                    "p99": 0
                }

            latencies = list(self._latencies)

            return {
                "count": len(latencies),
                "mean": sum(latencies) / len(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "p50": self._calculate_percentile(self._latencies, 50),
                "p95": self._calculate_percentile(self._latencies, 95),
                "p99": self._calculate_percentile(self._latencies, 99)
            }

    def get_agent_stats(self) -> Dict:

        with self._lock:
            stats = {}

            for agent, latencies in self._agent_latencies.items():
                if latencies:
                    stats[agent] = {
                        "count": len(latencies),
                        "mean_latency": sum(latencies) / len(latencies),
                        "min_latency": min(latencies),
                        "max_latency": max(latencies)
                    }

            return stats

    def get_route_distribution(self) -> Dict:

        with self._lock:
            total = sum(self._route_counts.values())

            if total == 0:
                return {}

            return {
                route: {
                    "count": count,
                    "percentage": round(count / total * 100, 2)
                }
                for route, count in self._route_counts.items()
            }

    def get_error_stats(self) -> Dict:

        with self._lock:
            return dict(self._error_counts)

    def get_token_stats(self) -> Dict:

        with self._lock:
            if not self._token_counts:
                return {
                    "count": 0,
                    "mean": 0,
                    "total": 0
                }

            tokens = list(self._token_counts)

            return {
                "count": len(tokens),
                "mean": sum(tokens) / len(tokens),
                "total": sum(tokens)
            }

    def get_success_rate(self) -> float:

        with self._lock:
            if self._query_count == 0:
                return 100.0

            return round(self._valid_count / self._query_count * 100, 2)

    def get_uptime(self) -> float:

        return round(time.time() - self._start_time, 2)

    def get_summary(self) -> Dict:

        return {
            "uptime_seconds": self.get_uptime(),
            "total_queries": self._query_count,
            "success_rate": self.get_success_rate(),
            "latency": self.get_latency_stats(),
            "tokens": self.get_token_stats(),
            "agent_performance": self.get_agent_stats(),
            "route_distribution": self.get_route_distribution(),
            "errors": self.get_error_stats(),
            "custom_metrics": {
                name: {
                    "count": len(values),
                    "mean": sum(values) / len(values) if values else 0
                }
                for name, values in self._custom_metrics.items()
            }
        }

    def reset(self):

        with self._lock:
            self._latencies.clear()
            self._agent_latencies.clear()
            self._route_counts.clear()
            self._error_counts.clear()
            self._query_count = 0
            self._valid_count = 0
            self._token_counts.clear()
            self._custom_metrics.clear()
            self._start_time = time.time()


class PerformanceTracker:

    def __init__(self):

        self._trackers = {}

    def start(self, operation: str) -> str:

        tracker_id = f"{operation}_{time.time()}"
        self._trackers[tracker_id] = {
            "operation": operation,
            "start_time": time.time()
        }
        return tracker_id

    def stop(self, tracker_id: str) -> Optional[float]:

        if tracker_id not in self._trackers:
            return None

        tracker = self._trackers.pop(tracker_id)
        latency_ms = (time.time() - tracker["start_time"]) * 1000

        return latency_ms

    def context_manager(self, operation: str):

        return TrackingContext(self, operation)


class TrackingContext:

    def __init__(self, tracker: PerformanceTracker, operation: str):

        self.tracker = tracker
        self.operation = operation
        self.tracker_id = None
        self.latency_ms = None

    def __enter__(self):

        self.tracker_id = self.tracker.start(self.operation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.latency_ms = self.tracker.stop(self.tracker_id)

        if exc_type:
            metrics.record_error(str(exc_type.__name__), self.operation)

        return False


metrics = MetricsCollector(window_size=10000)
tracker = PerformanceTracker()
