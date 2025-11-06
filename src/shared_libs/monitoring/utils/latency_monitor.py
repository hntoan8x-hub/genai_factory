# src/shared_libs/monitoring/utils/latency_monitor.py (FINAL PRODUCTION CODE)

import logging
import time
import asyncio
from typing import Dict, Any, Optional
from prometheus_client import Histogram # Import Prometheus

logger = logging.getLogger(__name__)

# --- METRICS DEFINITION (PROMETHEUS HARDENING) ---
LATENCY_HISTOGRAM = Histogram(
    'genai_request_latency_seconds', 
    'Latency of core inference operations', 
    labelnames=['operation', 'model'],
    # Buckets: 100ms, 500ms, 1s, 2s, 5s, 10s
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf')) 
)

class LatencyMonitor:
    """Tracks request latency for performance monitoring using Prometheus Histogram."""
    
    # Không cần __init__ phức tạp vì nó là một Utility gắn với Prometheus

    async def async_log_latency(self, operation_name: str, duration_seconds: float, model_name: str, request_id: str):
        """
        Asynchronously records latency metrics to Prometheus.
        """
        LATENCY_HISTOGRAM.labels(operation=operation_name, model=model_name).observe(duration_seconds)
        
        logger.info("Latency logged to Prometheus.", extra={
            'request_id': request_id,
            'metric': operation_name,
            'duration_s': round(duration_seconds, 4)
        })

    # Tiện ích Context Manager Bất đồng bộ (Hardening)
    class Timer:
        """Sử dụng cú pháp 'async with' để đo thời gian hoạt động."""
        def __init__(self, monitor: 'LatencyMonitor', operation_name: str, model_name: str, request_id: str):
            self.monitor = monitor
            self.operation_name = operation_name
            self.model_name = model_name
            self.request_id = request_id
            self.start_time = 0.0

        async def __aenter__(self):
            self.start_time = time.time()
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            await self.monitor.async_log_latency(self.operation_name, duration, self.model_name, self.request_id)