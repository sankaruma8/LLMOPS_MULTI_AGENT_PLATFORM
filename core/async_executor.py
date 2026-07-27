import asyncio
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Coroutine
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from collections import deque
import queue


class AsyncTaskQueue:

    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):

        self.max_workers = max_workers
        self.max_queue_size = max_queue_size

        self._task_queue = asyncio.Queue(maxsize=max_queue_size)
        self._results: Dict[str, Any] = {}
        self._task_status: Dict[str, str] = {}
        self._workers: List[asyncio.Task] = []
        self._running = False

        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_latency_ms": 0,
            "latencies": deque(maxlen=1000)
        }

    async def _worker(self, worker_id: int):

        while self._running:
            try:

                task_id, func, args, kwargs = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )

                self._task_status[task_id] = "running"

                start_time = time.time()

                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    self._results[task_id] = {
                        "status": "completed",
                        "result": result
                    }
                    self._task_status[task_id] = "completed"
                    self._stats["completed_tasks"] += 1

                except Exception as e:
                    self._results[task_id] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    self._task_status[task_id] = "failed"
                    self._stats["failed_tasks"] += 1

                latency_ms = (time.time() - start_time) * 1000
                self._stats["latencies"].append(latency_ms)

                if self._stats["latencies"]:
                    self._stats["avg_latency_ms"] = sum(self._stats["latencies"]) / len(self._stats["latencies"])

                self._task_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")

    async def start(self):

        if self._running:
            return

        self._running = True

        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

    async def stop(self):

        self._running = False

        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None
    ) -> str:

        if self._task_queue.full():
            raise RuntimeError("Task queue is full")

        kwargs = kwargs or {}

        self._stats["total_tasks"] += 1
        self._task_status[task_id] = "queued"

        await self._task_queue.put((task_id, func, args, kwargs))

        return task_id

    async def get_result(self, task_id: str, timeout: float = 30.0) -> Optional[Dict]:

        start_time = time.time()

        while time.time() - start_time < timeout:
            if task_id in self._results:
                return self._results.pop(task_id)

            if self._task_status.get(task_id) == "failed":
                return self._results.pop(task_id)

            await asyncio.sleep(0.1)

        return {"status": "timeout"}

    def get_stats(self) -> Dict:

        return {
            "total_tasks": self._stats["total_tasks"],
            "completed_tasks": self._stats["completed_tasks"],
            "failed_tasks": self._stats["failed_tasks"],
            "queue_size": self._task_queue.qsize(),
            "avg_latency_ms": round(self._stats["avg_latency_ms"], 2),
            "workers": self.max_workers,
            "running": self._running
        }


class SyncWorkerPool:

    def __init__(self, max_workers: int = None):

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }

    def submit(self, func: Callable, *args, **kwargs):

        self._stats["total_tasks"] += 1

        future = self._executor.submit(func, *args, **kwargs)

        def callback(future):
            if future.exception():
                self._stats["failed_tasks"] += 1
            else:
                self._stats["completed_tasks"] += 1

        future.add_done_callback(callback)

        return future

    def shutdown(self, wait: bool = True):

        self._executor.shutdown(wait=wait)

    def get_stats(self) -> Dict:

        return self._stats.copy()


class ProcessWorkerPool:

    def __init__(self, max_workers: int = None):

        self._executor = ProcessPoolExecutor(max_workers=max_workers)
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }

    def submit(self, func: Callable, *args, **kwargs):

        self._stats["total_tasks"] += 1

        future = self._executor.submit(func, *args, **kwargs)

        def callback(future):
            if future.exception():
                self._stats["failed_tasks"] += 1
            else:
                self._stats["completed_tasks"] += 1

        future.add_done_callback(callback)

        return future

    def shutdown(self, wait: bool = True):

        self._executor.shutdown(wait=wait)

    def get_stats(self) -> Dict:

        return self._stats.copy()


class RateLimitedExecutor:

    def __init__(self, max_per_second: int = 10, burst: int = 20):

        self.max_per_second = max_per_second
        self.burst = burst

        self._tokens = burst
        self._last_refill = time.time()
        self._lock = threading.Lock()

        self._executor = ThreadPoolExecutor(max_workers=max_per_second)

    def _refill_tokens(self):

        now = time.time()
        elapsed = now - self._last_refill

        self._tokens = min(
            self.burst,
            self._tokens + elapsed * self.max_per_second
        )
        self._last_refill = now

    def execute(self, func: Callable, *args, **kwargs):

        with self._lock:
            self._refill_tokens()

            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self.max_per_second
                time.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1

        return self._executor.submit(func, *args, **kwargs)

    def shutdown(self):

        self._executor.shutdown()


async_task_queue = AsyncTaskQueue(max_workers=10, max_queue_size=1000)
sync_worker_pool = SyncWorkerPool(max_workers=4)
rate_limited_executor = RateLimitedExecutor(max_per_second=20, burst=30)
