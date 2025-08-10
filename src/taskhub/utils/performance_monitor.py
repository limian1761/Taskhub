"""
Performance monitoring and metrics collection for Taskhub MCP server.
"""

import time
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps
from contextlib import contextmanager
import asyncio
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collect and track performance metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float("inf"),
            "max_time": 0.0,
            "errors": 0,
            "last_10_times": deque(maxlen=10)
        })
        self._lock = threading.Lock()
    
    def record_call(self, operation: str, duration: float, error: bool = False) -> None:
        """Record a function call duration."""
        with self._lock:
            metric = self.metrics[operation]
            metric["count"] += 1
            metric["total_time"] += duration
            metric["avg_time"] = metric["total_time"] / metric["count"]
            metric["min_time"] = min(metric["min_time"], duration)
            metric["max_time"] = max(metric["max_time"], duration)
            metric["last_10_times"].append(duration)
            if error:
                metric["errors"] += 1
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific operation or all operations."""
        with self._lock:
            if operation:
                return dict(self.metrics.get(operation, {}))
            return {op: dict(metrics) for op, metrics in self.metrics.items()}
    
    def reset_metrics(self, operation: Optional[str] = None) -> None:
        """Reset metrics for a specific operation or all operations."""
        with self._lock:
            if operation:
                self.metrics.pop(operation, None)
            else:
                self.metrics.clear()


# Global metrics instance
_metrics = PerformanceMetrics()


def monitor_performance(operation_name: Optional[str] = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                error = False
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = True
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    _metrics.record_call(name, duration, error)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                error = False
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = True
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    _metrics.record_call(name, duration, error)
            return sync_wrapper
    
    return decorator


@contextmanager
def performance_context(operation_name: str):
    """Context manager for measuring performance."""
    start_time = time.perf_counter()
    error = False
    try:
        yield
    except Exception as e:
        error = True
        raise
    finally:
        duration = time.perf_counter() - start_time
        _metrics.record_call(operation_name, duration, error)


def get_performance_summary() -> Dict[str, Any]:
    """Get a summary of all performance metrics."""
    return {
        "metrics": _metrics.get_metrics(),
        "timestamp": time.time(),
        "uptime_seconds": time.time() - _metrics.get_metrics("__startup_time").get("total_time", time.time())
    }


def reset_performance_metrics(operation: Optional[str] = None) -> None:
    """Reset performance metrics."""
    _metrics.reset_metrics(operation)


# Record startup time
_metrics.record_call("__startup_time", 0.0)


# Export commonly used functions
__all__ = [
    "monitor_performance",
    "performance_context",
    "get_performance_summary",
    "reset_performance_metrics",
    "PerformanceMetrics"
]