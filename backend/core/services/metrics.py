"""
Lightweight Prometheus-compatible metrics collector.
No external dependencies — memory-bounded, thread-safe.
"""

import threading
import time
from collections import defaultdict, deque


class MetricsCollector:
    """Singleton metrics collector producing Prometheus text format."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._gauges: dict[str, float] = {}
                    cls._instance._counters: dict[str, float] = defaultdict(float)
                    cls._instance._histograms: dict[str, deque] = defaultdict(
                        lambda: deque(maxlen=1000)
                    )
                    cls._instance._data_lock = threading.Lock()
        return cls._instance

    def gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        key = self._key(name, labels)
        with self._data_lock:
            self._gauges[key] = value

    def counter_inc(self, name: str, labels: dict | None = None, amount: float = 1) -> None:
        key = self._key(name, labels)
        with self._data_lock:
            self._counters[key] += amount

    def histogram_observe(self, name: str, value: float, labels: dict | None = None) -> None:
        key = self._key(name, labels)
        with self._data_lock:
            self._histograms[key].append(value)

    def collect(self) -> str:
        """Produce Prometheus text exposition format."""
        lines = []
        with self._data_lock:
            for key, value in sorted(self._gauges.items()):
                lines.append(f"{key} {value}")
            for key, value in sorted(self._counters.items()):
                lines.append(f"{key} {value}")
            for key, values in sorted(self._histograms.items()):
                if values:
                    sorted_vals = sorted(values)
                    count = len(sorted_vals)
                    total = sum(sorted_vals)
                    lines.append(f"{key}_count {count}")
                    lines.append(f"{key}_sum {total:.6f}")
                    # Quantiles
                    for q in (0.5, 0.9, 0.99):
                        idx = min(int(q * count), count - 1)
                        lines.append(f'{key}{{quantile="{q}"}} {sorted_vals[idx]:.6f}')
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _key(name: str, labels: dict | None = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Module-level singleton access
metrics = MetricsCollector()


def timed(metric_name: str, labels: dict | None = None):
    """Context manager to record duration as a histogram observation."""

    class Timer:
        def __enter__(self):
            self.start = time.monotonic()
            return self

        def __exit__(self, *args):
            duration = time.monotonic() - self.start
            metrics.histogram_observe(metric_name, duration, labels)

    return Timer()
