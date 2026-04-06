from typing import Dict, Any, List
from src.telemetry.logger import logger


PRICING = {
    "gpt-4o":        {"input": 0.0025, "output": 0.0100},
    "gpt-4o-mini":   {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}


class PerformanceTracker:
    """Tracks token usage, latency, and estimated cost per LLM call."""

    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(self, model: str, usage: Dict[str, int], latency_ms: int):
        pricing = PRICING.get(model, {"input": 0.01, "output": 0.01})
        input_cost = (usage.get("prompt_tokens", 0) / 1000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * pricing["output"]

        metric = {
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_usd": round(input_cost + output_cost, 6),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def get_summary(self) -> Dict[str, Any]:
        if not self.session_metrics:
            return {"total_requests": 0}

        latencies = [m["latency_ms"] for m in self.session_metrics]
        return {
            "total_requests": len(self.session_metrics),
            "total_tokens": sum(m["total_tokens"] for m in self.session_metrics),
            "total_cost_usd": round(sum(m["cost_usd"] for m in self.session_metrics), 6),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
            "max_latency_ms": max(latencies),
        }


tracker = PerformanceTracker()
