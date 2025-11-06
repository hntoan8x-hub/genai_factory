# src/shared_libs/monitoring/healthcheckers/llm_checker.py
import asyncio
from typing import Dict, Any
from shared_libs.monitoring.contracts.base_health_checker import BaseHealthChecker

class LLMHealthChecker(BaseHealthChecker):
    async def async_check_health(self) -> Dict[str, Any]:
        await asyncio.sleep(0.1) # Giả lập I/O
        # Logic: Ping/gọi một endpoint LLM đơn giản
        if True: # MOCK: Giả định luôn OK
             return {"status": "ok", "response_time_ms": 150}
        else:
             return {"status": "unhealthy", "error": "LLM API connection failed"}