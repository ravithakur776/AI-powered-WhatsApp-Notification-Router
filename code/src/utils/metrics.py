"""Metrics tracker for recording timing latency, token counts, and hit rates."""

import time
from typing import Dict, List
import numpy as np


class MetricsTracker:
    def __init__(self):
        self.fast_path_hits: int = 0
        self.deep_path_hits: int = 0
        self.latencies_ms: List[float] = []
        self.fast_path_latencies_ms: List[float] = []
        self.deep_path_latencies_ms: List[float] = []
        self.total_tokens_used: int = 0
        self.decisions_count: Dict[str, int] = {"notify": 0, "digest": 0, "mute": 0}

    def record_decision(self, action: str, latency_ms: float, is_fast_path: bool, tokens: int = 0):
        if action in self.decisions_count:
            self.decisions_count[action] += 1
        
        self.latencies_ms.append(latency_ms)
        if is_fast_path:
            self.fast_path_hits += 1
            self.fast_path_latencies_ms.append(latency_ms)
        else:
            self.deep_path_hits += 1
            self.deep_path_latencies_ms.append(latency_ms)
            self.total_tokens_used += tokens

    def get_summary(self) -> Dict[str, float]:
        total = self.fast_path_hits + self.deep_path_hits
        if total == 0:
            return {"total_messages": 0}

        return {
            "total_messages": total,
            "fast_path_ratio": round(self.fast_path_hits / total, 4),
            "deep_path_ratio": round(self.deep_path_hits / total, 4),
            "p50_latency_ms": round(float(np.percentile(self.latencies_ms, 50)), 2) if self.latencies_ms else 0.0,
            "p90_latency_ms": round(float(np.percentile(self.latencies_ms, 90)), 2) if self.latencies_ms else 0.0,
            "p99_latency_ms": round(float(np.percentile(self.latencies_ms, 99)), 2) if self.latencies_ms else 0.0,
            "fast_path_avg_latency_ms": round(float(np.mean(self.fast_path_latencies_ms)), 2) if self.fast_path_latencies_ms else 0.0,
            "deep_path_avg_latency_ms": round(float(np.mean(self.deep_path_latencies_ms)), 2) if self.deep_path_latencies_ms else 0.0,
            "total_tokens_used": self.total_tokens_used,
            "decisions_breakdown": self.decisions_count
        }


metrics_collector = MetricsTracker()
