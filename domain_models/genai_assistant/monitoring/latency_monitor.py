import time
from typing import Dict, Any

class LatencyMonitor:
    """
    Monitors and reports on the latency of various operations.
    
    Tracks latency for API calls, pipeline runs, and tool executions.
    """
    
    def __init__(self):
        """Initializes storage for latency metrics."""
        self.metrics: Dict[str, list] = {}
        
    def start_timer(self, metric_name: str) -> float:
        """Starts a timer for a given metric."""
        return time.time()

    def stop_timer(self, metric_name: str, start_time: float) -> float:
        """
        Stops a timer and records the elapsed time.
        
        Args:
            metric_name (str): The name of the metric.
            start_time (float): The start time returned by start_timer.
            
        Returns:
            float: The elapsed time in seconds.
        """
        end_time = time.time()
        latency = end_time - start_time
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(latency)
        return latency

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Calculates and returns summary statistics (p50, p95) for all metrics.
        """
        summary = {}
        for metric_name, latencies in self.metrics.items():
            if not latencies:
                continue
            latencies.sort()
            p50 = latencies[int(len(latencies) * 0.50)]
            p95 = latencies[int(len(latencies) * 0.95)]
            summary[metric_name] = {"p50": p50, "p95": p95}
        return summary
