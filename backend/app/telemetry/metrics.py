"""
Performance Metrics Tracker.

Person 5 owns this file.
Tracks request counts, latencies, tool usage, and cache hit rates.
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

    def get_summary(self) -> Dict:
        avg_latency = (
            sum(self.latencies_ms) / len(self.latencies_ms)
            if self.latencies_ms else 0
        )
        return {
            "total_requests": self.total_requests,
            "total_problems_solved": self.total_problems_solved,
            "total_cache_hits": self.total_cache_hits,
            "total_errors": self.total_errors,
            "avg_latency_ms": round(avg_latency, 1),
            "tool_usage": dict(self.tool_usage),
            "route_usage": dict(self.route_usage),
        }


# Global metrics tracker
metrics = MetricsTracker()
