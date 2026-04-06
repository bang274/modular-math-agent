"""
Performance Metrics Tracker.

Person 5 owns this file.
Tracks request counts, latencies, tool usage, and cache hit rates.
Provides p50/p95/p99 percentile calculations.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MetricsTracker:
    """In-memory metrics for monitoring pipeline performance."""

    total_requests: int = 0
    total_problems_solved: int = 0
    total_cache_hits: int = 0
    total_errors: int = 0

    latencies_ms: List[int] = field(default_factory=list)
    tool_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    route_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    _start_time: float = field(default_factory=time.time)

    def record_request(self, num_problems: int = 1) -> None:
        self.total_requests += 1
        self.total_problems_solved += num_problems

    def record_latency(self, latency_ms: int) -> None:
        self.latencies_ms.append(latency_ms)

    def record_tool(self, tool_name: str) -> None:
        self.tool_usage[tool_name] += 1

    def record_route(self, route: str) -> None:
        self.route_usage[route] += 1

    def record_cache_hit(self) -> None:
        self.total_cache_hits += 1

    def record_error(self) -> None:
        self.total_errors += 1

    # ── Percentile helpers ───────────────────────────────────

    def _percentile(self, data: List[int], pct: float) -> float:
        """Calculate the p-th percentile of a sorted list."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (pct / 100.0)
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return float(sorted_data[f])
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    # ── Summary ──────────────────────────────────────────────

    def get_summary(self) -> Dict:
        avg_latency = (
            sum(self.latencies_ms) / len(self.latencies_ms)
            if self.latencies_ms else 0
        )
        error_rate = (
            (self.total_errors / self.total_requests * 100)
            if self.total_requests > 0 else 0.0
        )
        uptime_seconds = round(time.time() - self._start_time)

        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": self.total_requests,
            "total_problems_solved": self.total_problems_solved,
            "total_cache_hits": self.total_cache_hits,
            "total_errors": self.total_errors,
            "error_rate_pct": round(error_rate, 2),
            "latency": {
                "avg_ms": round(avg_latency, 1),
                "p50_ms": round(self._percentile(self.latencies_ms, 50), 1),
                "p95_ms": round(self._percentile(self.latencies_ms, 95), 1),
                "p99_ms": round(self._percentile(self.latencies_ms, 99), 1),
            },
            "tool_usage": dict(self.tool_usage),
            "route_usage": dict(self.route_usage),
        }


# Global metrics tracker
metrics = MetricsTracker()
